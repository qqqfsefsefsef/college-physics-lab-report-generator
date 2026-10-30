r"""跑通「识别 → 计算 → 出 docx → 下载」：全程走 HTTP，和浏览器一模一样。

桥用 --mock 起（不需要 key），图片用工作区的真素材。
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


def post(path, obj, timeout=180):
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


def main():
    srv = subprocess.Popen([PY, BRIDGE, '--mock'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not wait_up():
            print('桥没起来')
            return
        img = os.path.join(SRC, 'IMG_20261026_213601.HEIC')
        raw = open(img, 'rb').read()
        print('输入：%s  %.2f MB' % (os.path.basename(img), len(raw) / 1e6))

        code, rec = post('/recognize', {'exp_id': 'photo',
                                        'image_b64': base64.b64encode(raw).decode('ascii'),
                                        'mime': 'image/heic'})
        print('① 识别  HTTP %s  %s' % (code, rec.get('meta', {}).get('image', {})))
        if code != 200:
            print('   error:', rec.get('error'))
            return

        code, ren = post('/render', {'exp_id': 'photo', 'tables': rec['tables']})
        print('② 出报告 HTTP %s' % code)
        if code != 200:
            print('   error:', ren.get('error'))
            return
        print('   project:', ren['project'], ' file:', ren['name'], ' %.1f KB' % (ren['bytes'] / 1024.0))
        r = ren['result']
        print('   h = %.4e J·s   rel = %+.2f%%   u(h) = %.2e   r = %.5f'
              % (r['h'], r['rel_err_pct'], r['u_h'], r['r']))

        code = 0
        with urllib.request.urlopen(BASE + ren['url'], timeout=60) as resp:
            blob = resp.read()
            code = resp.status
            disp = resp.headers.get('Content-Disposition')
        print('③ 下载  HTTP %s  %.1f KB  %s' % (code, len(blob) / 1024.0, disp))
        out = os.path.join(W, '05_成品_报告', '光电效应的研究_网页流水线版.docx')
        open(out, 'wb').write(blob)
        print('   已存到', out)
    finally:
        srv.terminate()


if __name__ == '__main__':
    main()
