# -*- coding: utf-8 -*-
r"""看 PROMPT 原文，准备加 detected_exp 字段。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\bridge.py'
s = io.open(P, encoding='utf-8').read()
i = s.find('PROMPT = ')
j = s.find('def table_brief')
if i < 0:
    i = s.find('PROMPT')
print(s[i:i + 1800])
print('---- table_brief ----')
print(s[j:j + 900])
