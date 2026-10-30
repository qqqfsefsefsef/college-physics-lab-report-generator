# -*- coding: utf-8 -*-
"""打印 bundle 里 /render 的真实报错。"""
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
time.sleep(0.3)

ed = bridge.experiments()['tungsten']
tables = bridge.mock_result(ed)['tables']
req = urllib.request.Request('http://127.0.0.1:%d/render' % port,
                             data=json.dumps({'exp_id': 'tungsten', 'tables': tables}).
                             encode('utf-8'),
                             headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        print(r.status, r.read().decode('utf-8')[:800])
except urllib.error.HTTPError as e:
    print('HTTP', e.code)
    print(e.read().decode('utf-8')[:2000])
srv.shutdown()
