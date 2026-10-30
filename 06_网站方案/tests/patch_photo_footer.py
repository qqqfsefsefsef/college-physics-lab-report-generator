# -*- coding: utf-8 -*-
r"""给 build_report.py 加页脚改写，然后重跑出光电效应报告 + 打印版 HTML。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\04_生成过程_脚本图表\build_report.py'
s = io.open(P, encoding='utf-8').read()
if "'长度测量'" in s and 'FTTEXT' in s:
    print('[SKIP] 已打过补丁')
else:
    old = 'doc.save(OUT)'
    new = """FTTEXT = '光电效应的研究'
for _sec in doc.sections:
    for _p in _sec.footer.paragraphs:
        for _r in _p.runs:
            if '长度测量' in _r.text:
                _r.text = _r.text.replace('长度测量', FTTEXT)
doc.save(OUT)"""
    assert s.count(old) == 1, 'doc.save 未命中'
    s = s.replace(old, new)
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
    print('[OK] 补丁已写入')
