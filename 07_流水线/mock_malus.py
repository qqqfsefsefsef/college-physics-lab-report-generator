# -*- coding: utf-8 -*-
"""验证马吕斯定律（实验 8）的示例数据。

数据按讲义表 1 排布：角度 α 0°～360°（每 10° 一挡）、cos²α、三次光功率读数、
平均光强 Ī 与归一化光强 Ī/I0。光强按 I = I0·cos²α + 暗计数 生成，再叠上
激光功率随时间的缓慢漂移和三次读数之间的小起伏，所有数字都保留两位小数。
另有 2 处「像真学生会写错」的笔误，notes 里给了定位（table/row/col/current/
candidates/why），页面会把它们列成待确认的题点。
"""

import math

I0_MW = 1.82          # 起偏器后线偏振光的光功率（mW）
DARK_MW = 0.021       # 暗计数与杂散光
DRIFT_PER_DEG = 0.00004   # 激光功率随旋转角缓慢下降（0.004 %/°）


def _reading(alpha, repeat):
    """第 repeat 次（1～3）在转角 alpha 处的光功率读数。"""
    base = I0_MW * math.cos(math.radians(alpha)) ** 2 + DARK_MW
    drift = 1.0 - DRIFT_PER_DEG * alpha
    wig = (0.004 * math.sin(math.radians(2.1 * alpha + 1.9 * repeat)) +
           0.003 * math.cos(math.radians(3.7 * alpha - 2.3 * repeat)))
    return '%.2f' % (base * drift + wig)


def _cos2(alpha):
    return '%.3f' % (math.cos(math.radians(alpha)) ** 2)


def mock(ed):
    angles = list(range(0, 361, 10))
    reads = [[_reading(a, r) for a in angles] for r in (1, 2, 3)]

    # 学生的两处笔误：90° 消光点的第三个读数小数点偏右一位；
    # 240° 的第二个读数把 0.47 写成了 0.64。
    reads[2][angles.index(90)] = '0.20'
    reads[1][angles.index(240)] = '0.64'

    means = []
    for j in range(len(angles)):
        vals = [float(reads[r][j]) for r in range(3)]
        means.append(sum(vals) / 3.0)
    i0 = max(means)
    norms = ['%.4f' % (m / i0) for m in means]

    rows = [
        ['角度 α/(°)'] + [str(a) for a in angles],
        ['cos²α'] + [_cos2(a) for a in angles],
        ['I_1/mW'] + reads[0],
        ['I_2/mW'] + reads[1],
        ['I_3/mW'] + reads[2],
        ['Ī/mW'] + ['%.3f' % m for m in means],
        ['Ī/I_0'] + norms,
    ]

    notes = [
        {'table': 't1', 'row': 4, 'col': 1 + angles.index(90),
         'where': 't1 第 5 行（I₃）第 11 列（α = 90°）',
         'current': '0.20', 'candidates': ['0.02'],
         'why': '消光位置三次读数 0.02、0.02、0.20，第三个数小数点偏右一位，'
                '像把 0.02 写成 0.20；照此平均会把消光点抬高约 0.06 mW，'
                '第一象限拟合的截距会明显偏大。'},
        {'table': 't1', 'row': 3, 'col': 1 + angles.index(240),
         'where': 't1 第 4 行（I₂）第 26 列（α = 240°）',
         'current': '0.64', 'candidates': ['0.46', '0.47'],
         'why': '同一角度另两次读数是 0.47、0.47，这一格 0.64 与 0.46 字形接近，'
                '且使 Ī 比两侧角度高出一截；按 0.47 左右取值更符合 I ∝ cos²α 的走向。'},
    ]

    return {'exp_id': ed.get('id', 'malus'),
            'tables': {'t1': {'cells': rows}},
            'notes': notes}
