# -*- coding: utf-8 -*-
"""① notes 候选值去重；② 桩数据的 notes 改成能定位到格子的结构（演示时也有题可做）。"""
import io

P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\bridge.py'
s = io.open(P, encoding='utf-8').read()
orig = s

# ---------- 1. 候选值去重 ----------
old = """        cands = [str(c).strip() for c in cands if str(c).strip() not in ('', 'None')]"""
new = """        seen_c = []
        for c in cands:
            v = str(c).strip()
            if v and v not in ('None',) and v not in seen_c:
                seen_c.append(v)
        cands = seen_c"""
assert old in s
s = s.replace(old, new, 1)

# ---------- 2. 钨桩：结构化 notes ----------
old = """                'notes': ['【桩】表 1 第 6 行第 8 列（0.725 A / 144 V）看着像 431，'
                          '但和同行 447 不单调，请人工确认。',
                          '【桩】表 2 第 8 行（T = 2.16×10³K）学生写在框线外，已按位置补入。']}"""
new = """                'notes': [
                    {'table': 't1', 'row': 5, 'col': 7,
                     'where': '表1 · I_f = 0.725 A · U_a = 144 V 那一格',
                     'current': '431', 'candidates': ['431', '447', '457'],
                     'why': '和同行 447 不单调，像是抄错了'},
                    {'table': 't2', 'row': 8, 'col': 4,
                     'where': '表2 · T = 2.16×10³K · √U_a = 9 那一格',
                     'current': '3.05', 'candidates': ['3.05', '3.06'],
                     'why': '学生写在了框线外，怕是外推截距不是这一行'}],
                }"""
assert old in s
s = s.replace(old, new, 1)

assert s != orig
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[OK] bridge notes polished, %d -> %d chars' % (len(orig), len(s)))
