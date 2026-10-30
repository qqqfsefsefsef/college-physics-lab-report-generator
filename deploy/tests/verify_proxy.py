# -*- coding: utf-8 -*-
"""
模拟线上拓扑：浏览器 → Caddy(handle_path /api/*) → bridge。

本机没有 Caddy，这里用一个 40 行的「剥掉 /api 前缀再转发」的代理顶替，
验证三件事：
  1) 页面把 BRIDGE 定成 https://域名/api 之后，请求路径形如 /api/health、/api/render
  2) 代理剥前缀后 bridge 能正常处理（bridge 本身不认识 /api）
  3) /render 返回的 url（/file?path=...）在前面拼 /api 之后仍然能下载

跑法：python deploy/tests/verify_proxy.py
"""
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(os.path.dirname(HERE), 'server', 'app')
PIPE = os.path.join(APP, 'pipeline')
os.environ['PIPE_GEN'] = os.path.join(APP, 'assets')
os.environ['PIPE_BASE'] = os.path.join(APP, 'assets', 'template.docx')
sys.path.insert(0, PIPE)

import bridge  # noqa: E402

upstream = bridge.ThreadingHTTPServer(('127.0.0.1', 0), bridge.Handler)
upstream.mock = True
UP = upstream.server_address[1]
threading.Thread(target=upstream.serve_forever, daemon=True).start()


class StripProxy(BaseHTTPRequestHandler):
    """等价于 Caddy 的 handle_path /api/*：把 /api 前缀去掉再转发。"""

    def log_message(self, *a):
        pass

    def _do(self, method):
        path = self.path
        if not path.startswith('/api/'):
            return self._send(404, {'error': 'proxy: 只转发 /api/*'})
        target = 'http://127.0.0.1:%d%s' % (UP, path[4:])          # 去掉 '/api'
        n = int(self.headers.get('Content-Length') or 0)
        body = self.rfile.read(n) if n else None
        req = urllib.request.Request(target, data=body, method=method,
                                     headers={'Content-Type': self.headers.get(
                                         'Content-Type') or 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
                self.send_response(r.status)
                for k in ('Content-Type', 'Content-Disposition'):
                    if r.headers.get(k):
                        self.send_header(k, r.headers[k])
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            self._send(e.code, json.loads(e.read().decode('utf-8') or '{}'))

    def _send(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._do('GET')

    def do_POST(self):
        self._do('POST')


proxy = ThreadingHTTPServer(('127.0.0.1', 0), StripProxy)
PX = proxy.server_address[1]
threading.Thread(target=proxy.serve_forever, daemon=True).start()
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


def call(path, obj=None):
    url = 'http://127.0.0.1:%d%s' % (PX, path)
    if obj is None:
        rq = urllib.request.Request(url)
    else:
        rq = urllib.request.Request(url, data=json.dumps(obj).encode('utf-8'),
                                    headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(rq, timeout=120) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)


st, body, _ = call('/api/health')
h = json.loads(body.decode('utf-8'))
check('GET /api/health', st == 200 and h.get('ok'), 'exps=%d' % len(h.get('experiments') or []))

ed = bridge.experiments()['photo']
st, body, _ = call('/api/render', {'exp_id': 'photo',
                                   'tables': bridge.mock_result(ed)['tables'],
                                   'provenance': {'source': 'mock'}})
j = json.loads(body.decode('utf-8'))
check('POST /api/render', st == 200 and j.get('ok'), '%d bytes' % (j.get('bytes') or 0))

# 页面里就是 BRIDGE + url，而 BRIDGE 已经带 /api → 请求路径 = /api/file?path=...
st2, data, hdrs = call('/api' + (j.get('url') or '/nope'))
check('GET /api/file 下载', st2 == 200 and len(data) == j.get('bytes'),
      '%d bytes  %s' % (len(data), hdrs.get('Content-Disposition', '')[:40]))

# 没有 /api 前缀的请求必须被挡（模拟直连 80 端口打到静态服务器的情况）
st3, _b, _h = call('/health')
check('未带前缀被拒', st3 == 404, 'status=%s' % st3)

upstream.shutdown()
proxy.shutdown()
print()
print('通过 %d 项，失败 %d 项' % (ok, len(bad)))
sys.exit(0 if not bad else 1)
