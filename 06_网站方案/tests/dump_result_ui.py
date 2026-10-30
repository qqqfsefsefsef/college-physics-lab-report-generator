# -*- coding: utf-8 -*-
"""打印结果页 HTML 片段与 fillResult 源码，供打补丁时对照。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(P, encoding='utf-8').read()

i = s.find('id="s-result"')
print('===== 结果页 HTML =====')
print(s[i - 120:i + 1200])

j = s.find('function fillResult')
k = s.find('\nfunction ', j + 10)
print('\n===== fillResult =====')
print(s[j:k])
