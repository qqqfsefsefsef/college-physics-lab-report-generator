# -*- coding: utf-8 -*-
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
S = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\sections_photo.py'
s = io.open(S, encoding='utf-8').read()
old = "[str(first + k) for k in range(8)]"
new = "[str(first + k) if k <= (z - a) else '' for k in range(8)]"
assert s.count(old) == 1, '表1 序号行未命中'
s = s.replace(old, new)
io.open(S, 'w', encoding='utf-8', newline='\n').write(s)
print('[OK] 表1 第三段序号列不再多写 24')
