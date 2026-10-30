# -*- coding: utf-8 -*-
"""清掉旧气泡墙的死代码：S5 已经没有 #chat 元素，buildReview() 里再取它会在示例模式下报错。"""
import io

P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(P, encoding='utf-8').read()
orig = s

# 1) buildReview 末尾：删掉写 #chat 的整段（从 var chat = $('chat'); 到紧随其后的闭包结束）
i = s.find("  var chat = $('chat');")
assert i > 0, 'chat block not found'
j = s.find("\n}\n", i)
assert j > i, 'end of buildReview not found'
tail = s[i:j]
assert 'addMsg(' in tail, 'unexpected block:\n' + tail[:300]
s = s[:i] + "  // 旧气泡墙已改成「表格下方选择题」，这里不再需要\n" + s[j + 1:]

# 2) 删掉 addMsg（只被旧气泡墙用）
a = s.find('function addMsg(who, text, id) {')
if a > 0:
    b = s.find('\n}\n', a)
    assert b > a
    s = s[:a] + s[b + 2:]

# 3) 删掉不再使用的 .chat/.msg 样式
for rule in ["  .chat{display:flex;flex-direction:column;gap:10px}\n"]:
    s = s.replace(rule, '')
for sel in ['.msg{max-width:92%;padding:10px 13px;']:
    k = s.find(sel)
    if k > 0:
        e = s.find('\n', k)
        s = s[:k] + s[e + 1:]

assert s != orig
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[OK] dead chat code removed: %d -> %d chars' % (len(orig), len(s)))
print('    still has $(\'chat\'):', "$('chat')" in s)
