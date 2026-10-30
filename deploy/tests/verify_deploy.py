# -*- coding: utf-8 -*-
"""
部署包自检（不联网）：
  1) deploy/server/app/pipeline 里的引擎能被 import
  2) 限流：第 9 次 /render 必须被拦
  3) 过期清理：造一个 8 天前的 web-* 目录，必须被删
  4) 真起一个 HTTP 服务：/health 200、tungsten /render 200 且能下载（图从 app/assets 来）
跑法：python deploy/tests/verify_deploy.py
"""
import io
import json
import os
import sys
import threading
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SRV = os.path.dirname(HERE)                       # deploy
APP = os.path.join(SRV, 'server', 'app')
PIPE = os.path.join(APP, 'pipeline')

os.environ['PIPE_GEN'] = os.path.join(APP, 'assets')
os.environ['PIPE_BASE'] = os.path.join(APP, 'assets', 'template.docx')
os.environ.setdefault('PROJECT_KEEP_DAYS', '7')
sys.path.insert(0, PIPE)

import bridge                                      # noqa: E402

ok = 0
bad = []


def check(name, cond, extra=''):
    global ok
    if cond:
        ok += 1
        print('[OK] %s %s' % (name, extra))
    else:
        bad.append(name)
        print('[FAIL] %s %s' % (name, extra))


# ---- 1) 资源齐不齐
exps = bridge.experiments()
check('实验定义', len(exps) == 11, '共 %d 套' % len(exps))
check('排版骨架', os.path.isfile(os.environ['PIPE_BASE']))
check('插图目录', len(os.listdir(os.path.join(APP, 'assets', 'figures'))) >= 3)

# ---- 2) 限流
lim = bridge.RL_RULES['render'][0]
for i in range(lim):
    o, _w = bridge.rate_ok('9.9.9.9', 'render')
    if not o:
        check('限流放行', False, '第 %d 次就被拦了' % (i + 1))
        break
else:
    o, wait = bridge.rate_ok('9.9.9.9', 'render')
    check('限流拦截', (o is False and wait > 0), '第 %d 次被拦，等 %ds' % (lim + 1, wait))

# ---- 3) 过期清理
proj = os.path.join(PIPE, 'projects')
os.makedirs(proj, exist_ok=True)
old = os.path.join(proj, 'web-old-test')
os.makedirs(old, exist_ok=True)
io.open(os.path.join(old, 'x.txt'), 'w', encoding='utf-8').write('x')
t = time.time() - 9 * 86400
os.utime(old, (t, t))
n = bridge.prune_projects(7)
check('过期清理', n >= 1 and not os.path.isdir(old), '删了 %d 个' % n)

# ---- 4) 真 HTTP
srv = bridge.ThreadingHTTPServer(('127.0.0.1', 0), bridge.Handler)
srv.mock = True
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)


def get(path):
    with urllib.request.urlopen('http://127.0.0.1:%d%s' % (port, path), timeout=60) as r:
        return r.status, r.read()


def post(path, obj):
    req = urllib.request.Request('http://127.0.0.1:%d%s' % (port, path),
                                 data=json.dumps(obj).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read().decode('utf-8') or '{}')
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8') or '{}')


st, body = get('/health')
h = json.loads(body.decode('utf-8'))
check('/health', st == 200 and h.get('ok'), 'mode=%s exps=%s' % (h.get('mode'), len(h.get('experiments') or [])))

mocked = bridge.mock_result(exps['tungsten'])
st, j = post('/render', {'exp_id': 'tungsten', 'tables': mocked['tables'],
                         'provenance': {'source': 'mock'}})
check('/render 200', st == 200 and j.get('ok'), '%d bytes' % (j.get('bytes') or 0))
check('/render 体积', (j.get('bytes') or 0) > 1_500_000, '（有 5 张图，应该 >1.5MB）')
if j.get('url'):
    st2, data = get(j['url'])
    check('/file 下载', st2 == 200 and len(data) == j['bytes'], '%d bytes' % len(data))

srv.shutdown()

print()
print('通过 %d 项，失败 %d 项' % (ok, len(bad)))
if bad:
    print('失败：' + '、'.join(bad))
sys.exit(0 if not bad else 1)
