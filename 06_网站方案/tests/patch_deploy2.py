# -*- coding: utf-8 -*-
"""把 BRIDGE/fetch 包装改成「在裸 Node 里 eval 也不炸」的防御式写法（不依赖 location / window.fetch）。"""
import io
import shutil
import sys

HP = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(HP, encoding='utf-8').read()
n0 = len(s)

old = """var BRIDGE = (function () {
  try { var s = localStorage.getItem('dsh.bridge'); if (s) return s.replace(/\\/+$/, ''); } catch (e) {}
  var h = location.hostname;
  if (h && h !== '127.0.0.1' && h !== 'localhost') return 'http://' + h + ':8732';
  return 'http://127.0.0.1:8732';
})();"""

new = """var BRIDGE = (function () {
  try { var s = localStorage.getItem('dsh.bridge'); if (s) return s.replace(/\\/+$/, ''); } catch (e) {}
  var h = '';
  try { h = (location && location.hostname) || ''; } catch (e) { h = ''; }
  if (h && h !== '127.0.0.1' && h !== 'localhost') return 'http://' + h + ':8732';
  return 'http://127.0.0.1:8732';
})();"""

c = s.count(old)
if c != 1:
    print('[FAIL] BRIDGE 锚点命中 %d 次' % c)
    sys.exit(1)
s = s.replace(old, new)
print('[OK] BRIDGE 防御式取 location')

old2 = """(function () {
  var raw = window.fetch.bind(window);"""
new2 = """(function () {
  if (typeof window === 'undefined' || !window.fetch) return;   /* 裸 Node 里跑测试时直接跳过 */
  var raw = window.fetch.bind(window);"""
c2 = s.count(old2)
if c2 != 1:
    print('[FAIL] fetch 包装锚点命中 %d 次' % c2)
    sys.exit(1)
s = s.replace(old2, new2)
print('[OK] fetch 包装加防御')

shutil.copyfile(HP, HP + '.bak7')
io.open(HP, 'w', encoding='utf-8', newline='\n').write(s)
print('[DONE] prototype_v2.html %d -> %d chars' % (n0, len(s)))
