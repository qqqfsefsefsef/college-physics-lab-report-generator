# -*- coding: utf-8 -*-
r"""看上传屏 S4 的标记与 pick/identify 接线。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(P, encoding='utf-8').read()
i = s.find('id="s-upload"')
j = s.find('id="s-review"')
print('---- S4 ----')
print(s[i - 60:i + 2600])
k = s.find('function pick(')
print('---- pick ----')
print(s[k:k + 1200])
