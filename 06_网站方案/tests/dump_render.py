# -*- coding: utf-8 -*-
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(P, encoding='utf-8').read()
i = s.find('function renderReport')
j = s.find('\nfunction ', i + 10)
print(s[i:j])
k = s.find('STATE.out')
print('---- 首次出现 STATE.out 附近 ----')
print(s[k - 200:k + 400])
