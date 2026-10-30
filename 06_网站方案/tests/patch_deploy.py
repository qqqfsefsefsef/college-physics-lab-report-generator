# -*- coding: utf-8 -*-
"""上线前置：bridge 地址可配置 + 访问口令（BRIDGE_TOKEN）+ 页面「连接设置」。

改两个文件：
  07_流水线\bridge.py          加 TOKEN 常量、CORS 放行 X-Token、do_POST 校验口令
  06_网站方案\prototype_v2.html  BRIDGE 动态取值、BRIDGE_TOKEN、fetch 包装自动带 X-Token、「连接设置」入口
"""
import io
import shutil
import sys

W = r'C:\Users\lidey\Desktop\实验报告制作沙盒'
BP = W + r'\07_流水线\bridge.py'
HP = W + r'\06_网站方案\prototype_v2.html'


def patch(path, pairs, backup):
    s = io.open(path, encoding='utf-8').read()
    n0 = len(s)
    for name, old, new in pairs:
        c = s.count(old)
        if c != 1:
            print('[FAIL] %s 锚点命中 %d 次：%s' % (path, c, name))
            sys.exit(1)
        s = s.replace(old, new)
        print('[OK] %s' % name)
    if backup:
        shutil.copyfile(path, path + backup)
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s)
    print('[DONE] %s  %d -> %d chars' % (path, n0, len(s)))


# ---------------------------------------------------------------- bridge.py
bp = [
    ('TOKEN 常量',
     "PORT = int(os.environ.get('BRIDGE_PORT', '8732'))\n",
     "PORT = int(os.environ.get('BRIDGE_PORT', '8732'))\n"
     "TOKEN = os.environ.get('BRIDGE_TOKEN', '').strip()   # 设了就要求请求头 X-Token\n"),

    ('CORS 放行 X-Token',
     "        self.send_header('Access-Control-Allow-Headers', 'Content-Type')\n",
     "        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Token')\n"),

    ('do_POST 校验口令',
     "        except Exception as e:\n"
     "            return self._json({'error': '请求体不是 JSON: %s' % e}, 400)\n"
     "\n"
     "        if path == '/detect':\n",
     "        except Exception as e:\n"
     "            return self._json({'error': '请求体不是 JSON: %s' % e}, 400)\n"
     "\n"
     "        if TOKEN and (self.headers.get('X-Token') or '').strip() != TOKEN:\n"
     "            return self._json({'error': '这个桥设了访问口令（BRIDGE_TOKEN）。'\n"
     "                                        '在页面右上角「连接设置」里填同一个口令。'}, 401)\n"
     "\n"
     "        if path == '/detect':\n"),
]

# ---------------------------------------------------------------- prototype
hp = [
    ('BRIDGE 动态 + TOKEN + fetch 包装',
     "var BRIDGE = 'http://127.0.0.1:8732';\n",
     "var BRIDGE = (function () {\n"
     "  try { var s = localStorage.getItem('dsh.bridge'); if (s) return s.replace(/\\/+$/, ''); } catch (e) {}\n"
     "  var h = location.hostname;\n"
     "  if (h && h !== '127.0.0.1' && h !== 'localhost') return 'http://' + h + ':8732';\n"
     "  return 'http://127.0.0.1:8732';\n"
     "})();\n"
     "var BRIDGE_TOKEN = (function () { try { return localStorage.getItem('dsh.token') || ''; } catch (e) { return ''; } })();\n"
     "/* 所有发往识别桥的请求自动带口令（BRIDGE_TOKEN 为空时行为不变） */\n"
     "(function () {\n"
     "  var raw = window.fetch.bind(window);\n"
     "  window.fetch = function (u, o) {\n"
     "    o = o || {};\n"
     "    if (typeof u === 'string' && u.indexOf(BRIDGE) === 0 && BRIDGE_TOKEN) {\n"
     "      var h = {};\n"
     "      var oh = o.headers || {};\n"
     "      for (var k in oh) if (Object.prototype.hasOwnProperty.call(oh, k)) h[k] = oh[k];\n"
     "      h['X-Token'] = BRIDGE_TOKEN;\n"
     "      o.headers = h;\n"
     "    }\n"
     "    return raw(u, o);\n"
     "  };\n"
     "})();\n"),

    ('顶栏加「连接设置」',
     '  <div class="sp"></div>\n'
     '  <a onclick="openNotice()">数据与结果说明</a>\n',
     '  <div class="sp"></div>\n'
     '  <a onclick="openNotice()">数据与结果说明</a>\n'
     '  <a onclick="setupConn()" title="识别桥地址与访问口令">连接设置</a>\n'),

    ('setupConn 函数',
     "function openNotice() {",
     "function setupConn() {\n"
     "  var b = window.prompt('识别桥地址（默认 http://127.0.0.1:8732；'\n"
     "    + '部署后用你的域名/隧道地址）', BRIDGE);\n"
     "  if (b === null) return;\n"
     "  b = String(b).trim().replace(/\\/+$/, '');\n"
     "  var t = window.prompt('访问口令（服务器没设 BRIDGE_TOKEN 就留空）', BRIDGE_TOKEN);\n"
     "  if (t === null) return;\n"
     "  t = String(t).trim();\n"
     "  try {\n"
     "    if (b) localStorage.setItem('dsh.bridge', b); else localStorage.removeItem('dsh.bridge');\n"
     "    if (t) localStorage.setItem('dsh.token', t); else localStorage.removeItem('dsh.token');\n"
     "  } catch (e) {}\n"
     "  location.reload();\n"
     "}\n"
     "\n"
     "function openNotice() {"),
]

patch(BP, bp, '.bak8')
patch(HP, hp, '.bak6')
print('\n全部完成。验证：')
print('  python -m py_compile bridge.py')
print('  node tests/check_wiring.js && node tests/check_flow.js')
