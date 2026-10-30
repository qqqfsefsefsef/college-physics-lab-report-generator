# -*- coding: utf-8 -*-
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(P, encoding='utf-8').read()

lines = s.split('\n')
hit = 0
for i, ln in enumerate(lines):
    if ln.strip().endswith("tn-ok.disabled = true;") and 'btn-ok' not in ln:
        lines[i] = "  $('btn-ok').disabled = true;"
        hit += 1
s2 = '\n'.join(lines)
if hit:
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s2)
print('fixed lines:', hit)
i = s2.find('function buildQuiz()')
print(s2[i:i + 430])
