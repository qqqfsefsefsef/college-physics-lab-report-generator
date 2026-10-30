# -*- coding: utf-8 -*-
"""用霍尔效应测磁场（实验 31）的桩数据：物理自洽的示例数据 + 两处“像学生会写错”的格子。

物理关系：V_H = K_H·I_s·B，K_H 取 250 mV/(mA·T)，B 按圆线圈/亥姆霍兹线圈轴上的解析式给出；
每组读数按对称测量法拆成 V1~V4，并叠加能斯特、里吉—勒杜克、不等势电位与埃廷斯豪森效应的小量。
R = 0.100 m、N = 500、I_M = 0.500 A、I_s = 5.00 mA，与讲稿的测量条件一致。

坐标约定（与讲稿“铜管位置调到 R 处、X 向读数以 O 为对称”一致）：
两线圈间距等于半径 R，中点 O 为 X 轴原点，线圈 1 中心在 x = −50 mm、线圈 2 中心在 +50 mm。
所以单线圈 1 的磁场峰值出现在 x = −50 mm 处，线圈 2 的在 +50 mm 处；两线圈同向串联时
B(R)(x) = B(1)(x) + B(2)(x)，可直接逐点相加验证叠加原理。
"""
import math

MU0 = 4e-7 * math.pi
N = 500
R = 0.100
I_M = 0.500
I_S = 5.00
K_TRUE = 250.0            # mV/(mA·T)
COIL1_MM = -50.0          # 线圈 1 中心（mm）
COIL2_MM = 50.0           # 线圈 2 中心（mm）
XS = [x for x in range(-120, 121, 10)]
HEAD = ['x/mm', 'V1/mV', 'V2/mV', 'V3/mV', 'V4/mV', 'V_H/mV', 'B/mT']


def b_single(d_mm):
    """单个圆线圈轴线上、距圆心 d 处的磁感应强度（mT）。"""
    d = d_mm / 1000.0
    return MU0 * N * I_M * R * R / (2.0 * (R * R + d * d) ** 1.5) * 1e3


def b_helm(z_mm):
    """两线圈中点 O 为原点时轴线上的磁感应强度（mT）。"""
    z = z_mm / 1000.0
    a = (R * R + (R / 2.0 + z) ** 2) ** 1.5
    b = (R * R + (R / 2.0 - z) ** 2) ** 1.5
    return 0.5 * MU0 * N * I_M * R * R * (1.0 / a + 1.0 / b) * 1e3


def _noise(i, scale):
    """确定性的小起伏，代替随机数，保证每次生成的数据完全一致。"""
    return scale * (math.sin(i * 2.17) * 0.6 + math.cos(i * 1.31) * 0.4)


def readings(b_mT, i, scale):
    v_h = K_TRUE * I_S * b_mT / 1000.0          # mV
    v_h += _noise(i, scale)
    v_e = 0.002 * v_h
    v_n = 0.0095 * b_mT
    v_rl = 0.0085 * b_mT
    v0 = 0.030
    v1 = round(v_h + v_e + v_n + v_rl + v0, 2)
    v2 = round(-v_h - v_e - v_n - v_rl + v0, 2)
    v3 = round(v_h + v_e - v_n - v_rl - v0, 2)
    v4 = round(-v_h - v_e + v_n + v_rl - v0, 2)
    return [v1, v2, v3, v4]


def _fmt(v):
    return '−%.2f' % abs(v) if v < 0 else '%.2f' % v


def _bump(s, delta):
    """把某一格按 delta 微调，模拟“末位数字抄错/压线看成别的数”。"""
    v = float(s.replace('−', '-')) + delta
    s2 = '%.2f' % v
    return s2.replace('-', '−')


def _table(b_fun, seed_scale, seed_phase):
    cells = [HEAD]
    for i, x in enumerate(XS):
        b = b_fun(x)
        vs = readings(b, i + seed_phase, seed_scale)
        vh = (vs[0] - vs[1] + vs[2] - vs[3]) / 4.0
        bt = vh / (K_TRUE * I_S) * 1000.0
        cells.append([str(x)] + [_fmt(v) for v in vs] + ['%.3f' % vh, '%.3f' % bt])
    return cells


def _recompute(cells):
    """注入错值后，重新计算 V_H 与 B 两列，保持表内自洽。"""
    for r in cells[1:]:
        vs = [float(str(v).replace('−', '-')) for v in r[1:5]]
        vh = (vs[0] - vs[1] + vs[2] - vs[3]) / 4.0
        r[5] = '%.3f' % vh
        r[6] = '%.3f' % (vh / (K_TRUE * I_S) * 1000.0)


def mock(ed):
    t1 = _table(lambda x: b_single(x - COIL1_MM), 0.012, 0)
    t2 = _table(lambda x: b_single(x - COIL2_MM), 0.014, 37)
    t3 = _table(b_helm, 0.010, 71)
    notes = []

    # 错点 1：表 1 中 x = −40 mm 的 V₁ 末位抄错（3 看成 5 一类）
    i = XS.index(-40)
    raw = t1[i + 1][1]
    wrong = _bump(raw, 0.02)
    t1[i + 1][1] = wrong
    notes.append({
        'table': 't1', 'row': i + 1, 'col': 1,
        'where': '表1 · x = −40 mm · V₁ 那一格',
        'current': wrong, 'candidates': [raw],
        'why': 'V₁ 应与同一行 V₂ 绝对值接近、且随位置平滑变化，这一格末位疑似看了个错数',
    })

    # 错点 2：表 3 中 x = +20 mm 的 V₃ 末位抄错
    j = XS.index(20)
    raw3 = t3[j + 1][3]
    wrong3 = _bump(raw3, 0.02)
    t3[j + 1][3] = wrong3
    notes.append({
        'table': 't3', 'row': j + 1, 'col': 3,
        'where': '表3 · x = +20 mm · V₃ 那一格',
        'current': wrong3, 'candidates': [raw3],
        'why': 'V₃ 对应 −I_s、−I_M，应为负值且与 V₁ 同量级，这一格末位与相邻点不连贯',
    })

    _recompute(t1)
    _recompute(t3)

    return {
        'exp_id': ed['id'],
        'tables': {'t1': {'cells': t1}, 't2': {'cells': t2}, 't3': {'cells': t3}},
        'notes': notes,
        'provenance': {'source': 'mock', 'generator': 'mock_hfield.py'},
    }
