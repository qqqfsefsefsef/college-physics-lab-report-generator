# -*- coding: utf-8 -*-
"""首页两个入口改成上下两行（居中堆叠）。"""
import io

P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(P, encoding='utf-8').read()
orig = s


def rep(old, new, tag):
    global s
    assert old in s, 'anchor not found: ' + tag
    assert s.count(old) == 1, 'anchor not unique: ' + tag
    s = s.replace(old, new, 1)


rep('  .paths{display:flex;gap:16px;width:min(820px,100%);margin-top:8px}',
    '  .paths{display:flex;flex-direction:column;gap:14px;width:min(520px,100%);margin-top:10px}',
    'paths')

rep('  .paths .pathcard{flex:1;text-align:left;display:flex;flex-direction:column;gap:8px}',
    '  .paths .pathcard{text-align:center;align-items:center;gap:6px;padding:18px 20px}',
    'pathcard')

rep('  @media(max-width:900px){.paths{flex-direction:column}.grid3{grid-template-columns:1fr}}',
    '  @media(max-width:900px){.grid3{grid-template-columns:1fr}}',
    'media')

assert s != orig
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[OK] home cards stacked: %d -> %d chars' % (len(orig), len(s)))
