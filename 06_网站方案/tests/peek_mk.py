# -*- coding: utf-8 -*-
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
s = io.open(r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\render_docx.py',
            encoding='utf-8').read()
i = s.find('def mk_run')
print(s[i:i + 900])
print('==== blocks ====')
j = s.find("t == 'para'")
print(s[max(0, j - 300):j + 900])
