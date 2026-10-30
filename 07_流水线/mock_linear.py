# -*- coding: utf-8 -*-
"""固体线膨胀系数的桩数据：铝棒 500.0 mm，水浴每级升温约 3 ℃。

读数按 α(铝) ≈ 2.30×10⁻⁵ ℃⁻¹ 取：ΔL ≈ α·L1·Δt，再留两处「像真学生会写错」的地方，
供识别页演示核对与纠正（notes 里给出定位、当前值与候选值）。
"""

L1_MM = 500.0
SET_C = [25.0, 28.0, 31.0, 34.0, 37.0, 40.0]        # 设定温度
T_C = [25.3, 27.2, 31.0, 33.9, 37.3, 40.0]          # 平衡后的实测温度（第 2 次是笔误）
L_UM = [150.0, 178.8, 215.5, 249.9, 288.1, 319.4]   # 千分表读数（第 4 次笔迹压线）


def mock(ed):
    dt = [round(t - T_C[0], 1) for t in T_C]
    dl = [round(l - L_UM[0], 1) for l in L_UM]

    def row(label, vals, dash_first=False):
        out = [label]
        for i, v in enumerate(vals):
            out.append('—' if (dash_first and i == 0) else v)
        return out

    cells = [
        ['次数', '1', '2', '3', '4', '5', '6'],
        row('设定温度/℃', SET_C),
        row('温度 t_i/℃', T_C),
        row('千分表读数 l_i/μm', L_UM),
        row('Δt_i/℃', dt, True),
        row('ΔL_i/μm', dl, True),
    ]
    t2 = [
        ['物理量', '测量值', '单位 / 误差限'],
        ['金属棒原长 L1', L1_MM, 'mm，±0.5'],
        ['千分表分度值', 0.001, 'mm'],
        ['温控仪分辨力', 0.1, '℃'],
    ]

    notes = [
        {'table': 't1', 'row': 2, 'col': 2,
         'where': '表1 · 第 2 次 · 温度 t_i/℃ 那一格',
         'current': '27.2', 'candidates': ['27.2', '27.8'],
         'why': '设定温度每次提高 3 ℃，这一格却只比前一组高 1.9 ℃；末位 2 与 8 的笔迹叠在一起。'
                '按铝的线膨胀量反算，第 2 次平衡温度应接近 27.8 ℃；改成 27.8 后六个点几乎落在一条直线上。'},
        {'table': 't1', 'row': 3, 'col': 4,
         'where': '表1 · 第 4 次 · 千分表读数 l_i/μm 那一格',
         'current': '249.9', 'candidates': ['248.9', '249.9'],
         'why': '中间的 8 被水渍糊成了 9；同组 ΔL_i 若记 99.9 μm，则第 3→4 次增量比相邻两次都大 1 μm，'
                '而千分表在一级 3 ℃ 升温内不会有这么大的跳变。'},
    ]
    return {'exp_id': ed['id'],
            'tables': {'t1': {'cells': cells}, 't2': {'cells': t2}},
            'notes': notes}
