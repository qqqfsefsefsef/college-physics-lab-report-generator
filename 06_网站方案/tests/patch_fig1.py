# -*- coding: utf-8 -*-
r"""给流水线版补上六张图（与直接生成版一致）。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
S = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\sections_photo.py'
s = io.open(S, encoding='utf-8').read()

# ---- 1. 顶部：os + GEN + _fig ----
if 'PIPE_GEN' not in s:
    anchor = 'def _ap(label):'
    assert s.count(anchor) == 1
    head = r'''import os

GEN = os.environ.get('PIPE_GEN',
                     r'C:\Users\lidey\Desktop\实验报告制作沙盒\04_生成过程_脚本图表')
FIG = os.path.join(GEN, 'figures')


def _fig(path, w, cap):
    return {'t': 'figure', 'path': path, 'width_cm': w, 'caption': cap}


'''
    s = s.replace(anchor, head + anchor)
    print('[OK] 加 GEN / FIG / _fig()')

# ---- 2. 仪器后插 图1 图2 ----
old = """    for line in md.get('仪器', []):
        B.append({'t': 'para', 'text': line})"""
new = """    for line in md.get('仪器', []):
        B.append({'t': 'para', 'text': line})
    B.append(_fig(os.path.join(GEN, 'fig_panel.png'), 13.1, '图1 普朗克实验仪前面板示意图'))
    B.append(_fig(os.path.join(GEN, 'fig_wiring.png'), 13.1, '图2 普朗克实验仪结构及接线示意图'))"""
assert s.count(old) == 1, '仪器段未命中'
s = s.replace(old, new)

# ---- 3. 原理后插 图3 光路 ----
old = """    for key in ('原理1', '原理2', '原理3', '原理4'):
        for line in md.get(key, []):
            B.append({'t': 'para', 'text': line})"""
new = """    for key in ('原理1', '原理2', '原理3', '原理4'):
        for line in md.get(key, []):
            B.append({'t': 'para', 'text': line})
    B.append(_fig(os.path.join(GEN, 'fig_light_path.png'), 11.2,
                  '图3 光电效应实验的光路与测量电路'))"""
assert s.count(old) == 1, '原理段未命中'
s = s.replace(old, new)

# ---- 4. 三张表后各插一张图 ----
old = """    B.append(T1)
    B.append({'t': 'caption', 'text': '表2 I_M—P 关系（U_AK＝30 V）', 'bold': True})
    B.append(T2)
    B.append({'t': 'caption', 'text': '表3 U₀~ν 关系测量（Φ＝2 mm）', 'bold': True})
    B.append(T3)"""
new = """    B.append(T1)
    B.append(_fig(os.path.join(FIG, 'fig_va.png'), 14.3, '图4 光电管的伏安特性曲线'))
    B.append({'t': 'caption', 'text': '表2 I_M—P 关系（U_AK＝30 V）', 'bold': True})
    B.append(T2)
    B.append(_fig(os.path.join(FIG, 'fig_ip.png'), 14.3, '图5 饱和电流与光阑孔面积的关系'))
    B.append({'t': 'caption', 'text': '表3 U₀~ν 关系测量（Φ＝2 mm）', 'bold': True})
    B.append(T3)
    B.append(_fig(os.path.join(FIG, 'fig_u0nu.png'), 14.3, '图6 截止电压与入射光频率的关系'))"""
assert s.count(old) == 1, '表段未命中'
s = s.replace(old, new)

io.open(S, 'w', encoding='utf-8', newline='\n').write(s)
print('[OK] 六张图已插入，文件 %d 字符' % len(s))
