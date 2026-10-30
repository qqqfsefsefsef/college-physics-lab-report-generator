# -*- coding: utf-8 -*-
"""验证「不剥 /api 前缀」的反代（Cloudflare 隧道按路径分流）也能用。"""
import json
import os
import sys
import threading
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(os.path.dirname(HERE), 'server', 'app')
PIPE = os.path.join(APP, 'pipeline')
os.environ['PIPE_GEN'] = os.path.join(APP, 'assets')
os.environ['PIPE_BASE'] = os.path.join(APP, 'assets', 'template.docx')
sys.path.insert(0, PIPE)

import bridge  # noqa: E402

srv = bridge.ThreadingHTTPServer(('127.0.0.1', 0), bridge.Handler)
srv.mock = True
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)

ok, bad = 0, []


def check(name, cond, extra=''):
    global ok
    if cond:
        ok += 1
        print('[OK] %s %s' % (name, extra))
    else:
        bad.append(name)
        print('[FAIL] %s %s' % (name, extra))


def call(path):
    url = 'http://127.0.0.1:%d%s' % (port, path)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


check('strip_api 纯函数', bridge.strip_api('/api/health') == '/health'
      and bridge.strip_api('/health') == '/health'
      and bridge.strip_api('/api') == '/')

st, body = call('/health')
check('不带前缀 /health', st == 200 and json.loads(body.decode('utf-8')).get('ok'))

st, body = call('/api/health')
check('带前缀 /api/health', st == 200 and json.loads(body.decode('utf-8')).get('ok'))

st, body = call('/api/usage?n=1')
check('带前缀 /api/usage', st == 200 and isinstance(json.loads(body.decode('utf-8')), (list, dict)))

srv.shutdown()
print()
print('通过 %d 项，失败 %d 项' % (ok, len(bad)))
sys.exit(0 if not bad else 1)
