"""端到端跑一遍「网页会走的同一条路」：读图 -> 规整 -> /recognize -> /calc。

不联网、不需要密钥：桥用 --mock 起在 8732，图片用工作区里的真素材。
"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

W = r'C:\Users\lidey\Desktop\实验报告制作沙盒'
SRC = os.path.join(W, '01_素材_数据与截图')
PY = sys.executable
BRIDGE = os.path.join(W, '07_流水线', 'bridge.py')
BASE = 'http://127.0.0.1:8732'


def post(path, obj, timeout=120):
    req = urllib.request.Request(BASE + path, data=json.dumps(obj).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8') or '{}')


def wait_up(sec=20):
    for _ in range(sec * 4):
        try:
            with urllib.request.urlopen(BASE + '/health', timeout=2) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception:
            time.sleep(0.25)
    return None


def run(exp_id, path, mime):
    name = os.path.basename(path)
    raw = open(path, 'rb').read()
    print('=' * 76)
    print('%s  (%s, %.2f MB)' % (name, mime, len(raw) / 1e6))
    t0 = time.time()
    code, res = post('/recognize', {'exp_id': exp_id, 'image_b64': base64.b64encode(raw).decode('ascii'),
                                    'mime': mime})
    dt = time.time() - t0
    print('  /recognize -> HTTP %s  (%.2fs)' % (code, dt))
    if code != 200:
        print('  error :', res.get('error'))
        print('  hint  :', res.get('hint'))
        return None
    meta = res.get('meta', {})
    print('  image :', json.dumps(meta.get('image', {}), ensure_ascii=False))
    t1 = res.get('tables', {}).get('t1', {})
    rows = t1.get('cells') or []
    print('  tables: t1 %dx%d, %s' % (len(rows), len(rows[0]) if rows else 0, list(res.get('tables', {}).keys())))
    if rows:
        print('  首行  :', rows[0])
    print('  notes :', len(res.get('notes', [])), (res.get('notes') or ['']) [0][:70])
    code2, c = post('/calc', {'exp_id': exp_id, 'tables': res['tables']})
    print('  /calc     -> HTTP %s' % code2)
    if code2 == 200:
        r = c.get('result', c)
        print('  result    :', json.dumps(r, ensure_ascii=False)[:300])
    else:
        print('  calc err  :', c.get('error'))
    return res


def main():
    srv = subprocess.Popen([PY, BRIDGE, '--mock'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        h = wait_up()
        if not h:
            print('桥没起来'); return
        print('bridge:', h['mode'], '| 已接入:', [e['name'] for e in h['experiments']])
        run('photo', os.path.join(SRC, 'IMG_20261026_213601.HEIC'), 'image/heic')
        run('tungsten', os.path.join(SRC, 'IMG_20261026_222018.HEIC'), 'image/heic')
        run('photo', os.path.join(SRC, 'Screenshot_2026-10-26-22-18-26-754_com.chaoxing.m.jpg'), 'image/jpeg')
    finally:
        srv.terminate()


if __name__ == '__main__':
    main()
