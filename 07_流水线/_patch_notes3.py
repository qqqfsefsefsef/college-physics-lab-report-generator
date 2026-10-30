# -*- coding: utf-8 -*-
"""光电效应桩数据也给出「能定位到格子」的题点，演示时选择题才有具体位置。"""
import io

P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\bridge.py'
s = io.open(P, encoding='utf-8').read()
orig = s

old = """                'notes': ['【桩】表 1 是 435.8 nm/2 mm 与 546.1 nm/4 mm 两组曲线；'
                          '577.0 nm 那一列三次读数差得有点大，已按原始记录保留。']}"""
new = """                'notes': [
                    {'table': 't1', 'row': 2, 'col': 1,
                     'where': '表1 · 546.1 nm / Φ=4 mm · U_AK = −4 V 那一格',
                     'current': '0.5', 'candidates': ['0.5', '0.4', '0.6'],
                     'why': '铅笔涂改过，看得出原来像 0.4'},
                    {'table': 't3', 'row': 4, 'col': 5,
                     'where': '表3 · 577.0 nm · 第 3 次读数 U₀ 那一格',
                     'current': '-0.176', 'candidates': ['-0.176', '-0.180', '-0.169'],
                     'why': '写了两遍划掉一遍，最后写定的是 -0.176'}],
                }"""
assert old in s
s = s.replace(old, new, 1)

assert s != orig
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[OK] photo mock notes ->', len(s), 'chars')
