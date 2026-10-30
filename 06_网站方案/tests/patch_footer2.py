# -*- coding: utf-8 -*-
r"""页脚跟着实验走：修调用点 + 给实验定义加 footer 短名。"""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
W = r'C:\Users\lidey\Desktop\实验报告制作沙盒'
B = W + r'\07_流水线\bridge.py'
T = W + r'\04_生成过程_脚本图表\build_report_tungsten.py'
Y = W + r'\07_流水线\experiments\young.json'
P = W + r'\07_流水线\experiments\photo.json'

# 1) bridge 传 footer
b = io.open(B, encoding='utf-8').read()
old = "render_docx.render(blocks, out, ed.get('name'))"
new = "render_docx.render(blocks, out, ed.get('name'),\n                           footer=ed.get('footer') or ed.get('name'))"
if b.count(old) == 1:
    b = b.replace(old, new)
    io.open(B, 'w', encoding='utf-8', newline='\n').write(b)
    print('[OK] bridge 传 footer')
else:
    print('[WARN] bridge 未命中', b.count(old))

# 2) 钨的自建渲染器：保存前改页脚
t = io.open(T, encoding='utf-8').read()
if "长度测量" not in t:
    old = "doc.save(OUT)"
    new = """for _sec in doc.sections:
    for _p in _sec.footer.paragraphs:
        for _r in _p.runs:
            if '长度测量' in _r.text:
                _r.text = _r.text.replace('长度测量', '钨的逸出功')
doc.save(OUT)"""
    assert t.count(old) == 1, 'doc.save 未命中'
    t = t.replace(old, new)
    io.open(T, 'w', encoding='utf-8', newline='\n').write(t)
    print('[OK] 钨脚本改页脚')

# 3) 实验定义加 footer 短名
for path, foot in ((Y, '杨氏模量'), (P, '光电效应的研究')):
    ed = json.load(io.open(path, encoding='utf-8'))
    if ed.get('footer') != foot:
        ed['footer'] = foot
        json.dump(ed, io.open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('[OK] %s footer=%s' % (path.split('\\')[-1], foot))
    else:
        print('[SKIP] %s 已有 footer' % path.split('\\')[-1])
