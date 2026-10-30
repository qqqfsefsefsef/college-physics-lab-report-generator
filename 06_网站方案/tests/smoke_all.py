# -*- coding: utf-8 -*-
"""11 套实验的端到端烟测：起临时桥（默认 8734）→ 逐个 /recognize(mock) → /render → 下载 → 关桥。

用法：python smoke_all.py [port]
"""
import base64
import glob
import io
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, '..', '..'))
PIPE = os.path.join(WORK, '07_流水线')
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8734
BASE = 'http://127.0.0.1:%d' % PORT
PY = sys.executable


def get(path, timeout=30):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return r.status, r.read()


def post(path, obj, timeout=180):
    data = json.dumps(obj).encode('utf-8')
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode('utf-8'))
        except Exception:
            return e.code, {'error': 'body not json'}


def main():
    ids = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(PIPE, 'experiments', '*.json')))
    fx = os.path.join(HERE, 'fixture.jpg')
    b64 = base64.b64encode(io.open(fx, 'rb').read()).decode('ascii')

    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'utf-8'
    p = subprocess.Popen([PY, os.path.join(PIPE, 'bridge.py'), '--port', str(PORT)],
                         cwd=PIPE, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ok = 0
    try:
        h = None
        for _ in range(60):
            try:
                st, body = get('/health', timeout=2)
                if st == 200:
                    h = json.loads(body.decode('utf-8'))
                    break
            except Exception:
                pass
            time.sleep(0.3)
        if not h:
            raise SystemExit('桥没起来')
        print('[OK] 桥已起 mode=%s，已接入 %d 个实验' % (h['mode'], len(h['experiments'])))

        for eid in ids:
            st, body = post('/recognize', {'exp_id': eid, 'mode': 'mock',
                                           'image_b64': b64, 'mime': 'image/jpeg'})
            if st != 200:
                print('[FAIL] %-10s recognize %s %s' % (eid, st, body.get('error')))
                continue
            tables = body['tables']
            shape = ' '.join('%s=%dx%d' % (k, len(v['cells']), len(v['cells'][0]))
                             for k, v in sorted(tables.items()))
            st2, rb = post('/render', {'exp_id': eid, 'tables': tables})
            if st2 != 200:
                print('[FAIL] %-10s render %s %s' % (eid, st2, rb.get('error')))
                continue
            st3, raw = get(rb['url'])
            ok += 1
            print('[OK] %-10s %-24s %7.1f KB  kpi=%-28s dl=%d  %s' % (
                eid, rb['name'], len(raw) / 1024.0,
                ' '.join(str(k.get('key')) for k in (rb.get('kpi') or [])), st3, shape))
        print('\n[SUM] %d/%d 通过' % (ok, len(ids)))
    finally:
        p.terminate()
        try:
            p.wait(timeout=10)
        except Exception:
            p.kill()
    return 0 if ok == len(ids) else 1


if __name__ == '__main__':
    sys.exit(main())
