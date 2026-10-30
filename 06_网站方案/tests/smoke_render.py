# -*- coding: utf-8 -*-
"""端到端烟测：起一个临时桥（不占 8732），对三个实验各跑一次 /render 并下载，最后关掉。

用法：python smoke_render.py [port]
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, '..', '..'))
PIPE = os.path.join(WORK, '07_流水线')
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8733
BASE = 'http://127.0.0.1:%d' % PORT
PY = sys.executable


def get(path, timeout=20):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return r.status, r.read()


def post(path, obj, timeout=120):
    data = json.dumps(obj).encode('utf-8')
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8'))


def wait_health(n=60):
    for _ in range(n):
        try:
            st, body = get('/health', timeout=2)
            if st == 200:
                return json.loads(body.decode('utf-8'))
        except Exception:
            pass
        time.sleep(0.3)
    raise SystemExit('桥没起来')


def main():
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'utf-8'
    p = subprocess.Popen([PY, os.path.join(PIPE, 'bridge.py'), '--port', str(PORT)],
                         cwd=PIPE, env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ok = 0
    try:
        h = wait_health()
        print('[OK] 桥已起 mode=%s experiments=%s' % (h['mode'], ','.join(e['id'] for e in h['experiments'])))
        tables = json.loads(get('/mock-tables')[1].decode('utf-8')) if False else None
        # 桩数据由 /recognize(mode=mock) 提供：先拿三份桩表（需要一个真图片来通过归一化）
        fx = os.path.join(HERE, 'fixture.jpg')
        if not os.path.exists(fx):
            fx = os.path.join(HERE, 'fixture.b64')
        if fx.endswith('.b64'):
            import base64
            b64 = open(fx, 'r', encoding='ascii').read().strip()
        else:
            import base64
            b64 = base64.b64encode(open(fx, 'rb').read()).decode('ascii')
        fixtures = {}
        for eid in ('photo', 'tungsten', 'young'):
            st, body = post('/recognize', {'exp_id': eid, 'mode': 'mock',
                                           'image_b64': b64, 'mime': 'image/jpeg'})
            if st != 200:
                print('[FAIL] %-8s recognize %s %s' % (eid, st, body.get('error')))
                continue
            fixtures[eid] = body['tables']
            print('[OK] %-8s 桩表 %s' % (eid, ' '.join('%s=%dx%d' % (k, len(v['cells']), len(v['cells'][0]))
                                                     for k, v in body['tables'].items())))
        for eid, tb in fixtures.items():
            st, body = post('/render', {'exp_id': eid, 'tables': tb})
            if st != 200:
                print('[FAIL] %-8s render %s %s' % (eid, st, body.get('error')))
                continue
            st2, raw = get(body['url'])
            size_kb = len(raw) / 1024.0
            ok += 1
            print('[OK] %-8s %s  %.1f KB  kpi=%s  dl=%d' % (
                eid, body['name'], size_kb,
                ' '.join(str(k.get('key')) for k in (body.get('kpi') or [])), st2))
        print('\n[SUM] %d/3 通过' % ok)
    finally:
        p.terminate()
        try:
            p.wait(timeout=10)
        except Exception:
            p.kill()
    return 0 if ok == 3 else 1


if __name__ == '__main__':
    sys.exit(main())
