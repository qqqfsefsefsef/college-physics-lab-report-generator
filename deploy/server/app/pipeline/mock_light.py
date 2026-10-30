# -*- coding: utf-8 -*-
"""光速测定（实验 49）的示例数据。

用调制波法测相位差求波长：载波频率 f = 100 MHz，示波器上把参考信号的一个周期
展开成 5 大格（1 大格 = 72°），读出移动反射镜后波形相移的格数 r，则
φ = 2πr/5，λ = 2π·2D/φ = 10D/r（D 以 m 计），c = λf。

表 1 为等间距法（x0～x4 等间距移动反射镜小车），表 2 为等相位法（每次移动
72°，并把反射镜拉回 0° 复测 X0′）。数据按 λ ≈ 3.03 m、c ≈ 3.03×10⁸ m/s
生成，与公认值相差约 1 %；另留 2 处「像真学生会写错」的点，notes 里给出定位。
"""

import math

F_HZ = 100e6          # 载波（调制）频率
R0 = 5.0              # 一个周期在示波器上占 5 大格
PHI_72 = math.radians(72.0)


def _lam(D_cm, r):
    """λ = 2π·2D/φ，其中 φ = 2πr/R0，故 λ = 2D·R0/r（D 用 m）。"""
    return 2.0 * (D_cm / 100.0) * R0 / r


def _phi(r):
    return 2.0 * math.pi * r / R0


def mock(ed):
    xs = [35.00, 50.00, 65.00, 80.00, 95.00]
    Ds = [0.00, 15.00, 30.00, 45.00, 61.00]
    rs = [0.00, 0.49, 0.99, 1.48, 1.98]

    lams = ['—']
    for i in range(1, len(xs)):
        lams.append('%.3f' % _lam(Ds[i], rs[i]))
    mean1 = sum(_lam(Ds[i], rs[i]) for i in range(1, len(xs))) / (len(xs) - 1)

    t1 = [
        ['位置', 'x_0', 'x_1', 'x_2', 'x_3', 'x_4'],
        ['读数/cm'] + ['%.2f' % v for v in xs],
        ['D_i/cm'] + ['%.2f' % v for v in Ds],
        ['r_i/格'] + ['%.2f' % v for v in rs],
        ['φ_i/rad'] + ['%.3f' % _phi(v) for v in rs],
        ['λ_i/m'] + lams,
        ['λ̄/m', '%.3f' % mean1, '', '', '', ''],
    ]

    X0 = [45.00, 45.04, 44.98]
    Xi = [75.30, 75.35, 75.28]
    X0p = [45.02, 45.06, 46.00]
    Xbar, D2, lam2 = [], [], []
    for a, b, c in zip(X0, Xi, X0p):
        xb = (a + c) / 2.0
        d = b - xb
        Xbar.append(xb)
        D2.append(d)
        lam2.append(4.0 * math.pi * (d / 100.0) / PHI_72)
    mean2 = sum(lam2) / len(lam2)

    t2 = [
        ['φ_i/(°)'] + ['72'] * 3,
        ['X_0/cm'] + ['%.2f' % v for v in X0],
        ['X_i/cm'] + ['%.2f' % v for v in Xi],
        ['X_0′/cm'] + ['%.2f' % v for v in X0p],
        ['X̄_0/cm'] + ['%.2f' % v for v in Xbar],
        ['D_i/cm'] + ['%.2f' % v for v in D2],
        ['λ_i/m'] + ['%.3f' % v for v in lam2],
        ['λ̄/m', '%.3f' % mean2, '', ''],
    ]

    notes = [
        {'table': 't1', 'row': 2, 'col': 5,
         'where': 't1 第 3 行（D_i/cm）第 6 列（x_4）',
         'current': '61.00', 'candidates': ['60.00'],
         'why': 'x_4 − x_0 = 95.00 − 35.00 = 60.00 cm，这一格却写成 61.00，'
                '像抄 D 时多加了 1 cm。按 61.00 算 λ_4 = 3.081 m，比相邻点的 3.03 m '
                '高出一截，把等间距法的平均波长抬高了约 1%，是 c 偏大的主要来源。'},
        {'table': 't2', 'row': 3, 'col': 3,
         'where': 't2 第 4 行（X_0′/cm）第 3 次测量',
         'current': '46.00', 'candidates': ['45.00', '45.02'],
         'why': '同一次的 X_0 = 44.98 cm，X_0′ 与它相差 1.02 cm，超过了讲义要求的'
                '「两次 0° 读数误差不超过 5 mm，否则须重测」。若 X_0′ 取 45.00，'
                'X̄_0 = 44.99 cm、D = 30.29 cm、λ = 3.029 m，平均波长由 3.013 m 回到 3.030 m。'},
    ]

    return {'exp_id': ed.get('id', 'light'),
            'tables': {'t1': {'cells': t1}, 't2': {'cells': t2}},
            'notes': notes}
