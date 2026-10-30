# -*- coding: utf-8 -*-
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
s = io.open(r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\render_docx.py',
            encoding='utf-8').read()
i = s.find('def _cell_setup')
print(s[i:i + 950])
print('==== dispatch ====')
j = s.find("t == 'table'")
print(s[max(0, j - 260):j + 620])
