# -*- coding: utf-8 -*-
"""给 bridge.py 加 --host 参数（默认 127.0.0.1），供局域网/公网部署时绑 0.0.0.0。"""
import io, os, shutil, sys

P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\bridge.py'
src = io.open(P, encoding='utf-8').read()
orig = src

if '--host' in src:
    print('[SKIP] 已经有 --host')
    sys.exit(0)

a = "    ap.add_argument('--port', type=int, default=PORT)\n"
b = ("    ap.add_argument('--port', type=int, default=PORT)\n"
     "    ap.add_argument('--host', default=os.environ.get('BRIDGE_HOST', '127.0.0.1'),\n"
     "                    help='监听地址；局域网/公网部署时用 0.0.0.0')\n")
assert src.count(a) == 1, src.count(a)
src = src.replace(a, b)
print('[OK] 加 --host 参数')

a2 = "    srv = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)\n"
b2 = "    srv = ThreadingHTTPServer((args.host, args.port), Handler)\n"
assert src.count(a2) == 1, src.count(a2)
src = src.replace(a2, b2)
print('[OK] 绑定地址改成 args.host')

a3 = "    print('[bridge] http://127.0.0.1:%d  mode=%s  model=%s  key=%s'\n"
idx = src.find(a3)
assert idx > 0, 'banner anchor not found'
seg_end = src.find('\n', src.find('))', idx)) if '))' in src[idx:idx+400] else -1
# 简单处理：把 banner 那一行里的 127.0.0.1 换成 args.host
line_end = src.find('\n', idx)
line = src[idx:line_end]
line2 = line.replace('http://127.0.0.1:', 'http://%s:' % '{host}')
line2 = line2.replace("%d  mode", "%d  mode")
src = src[:idx] + line2 + src[line_end:]
print('[OK] banner 改成 args.host')

shutil.copyfile(P, P + '.bak7')
io.open(P, 'w', encoding='utf-8', newline='\n').write(src)
print('[DONE] bridge.py %d -> %d chars' % (len(orig), len(src)))
