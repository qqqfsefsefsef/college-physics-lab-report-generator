# -*- coding: utf-8 -*-
"""霍尔效应及其应用（实验 30）的桩数据：物理自洽的示例数据 + 两处“像学生会写错”的格子。

物理关系：V_H = K_H·I_s·B，取 a-GaAs 类霍尔元件（n ≈ 2×10²¹ m⁻³、d = 0.2 mm），
K_H = 1/(n e d) ≈ 15.6 mV/(mA·T)；电磁铁的 B–I_M 近似线性，带一点饱和；
四组读数按对称测量法拆成 V1~V4，叠加埃廷斯豪森、能斯特、里吉—勒杜克与不等势电压的小量。
电导率由五端引线的 U_AC–I 直线给出，σ = I·l/(U_AC·S)，迁移率 μ = |R_H|·σ。
"""
import math

N_TRUE = 2.0e21          # m⁻³
D_M = 2.0e-4             # m
L_M = 1.5e-3             # m，A、C 电极间距
B_M = 1.5e-3             # m，元件宽度
E_CHARGE = 1.602e-19
R_H_TRUE = 1.0 / (N_TRUE * E_CHARGE)          # m³/C
K_H_TRUE = R_H_TRUE / D_M                     # V/(A·T) = mV/(mA·T)
SIGMA_TRUE = 112.0                            # S/m
U_PER_MA = L_M / (SIGMA_TRUE * B_M * D_M)     # V/A → 乘以 mA 得 mV：44.64
I_S_T1 = [0.50, 1.00, 1.50, 2.00, 2.50, 3.00]
IM_T2 = [50, 100, 150, 200, 250, 300, 350, 400, 450, 500]
IM_T3 = list(IM_T2)
HEAD_V = ['I_s/mA', 'V1/mV', 'V2/mV', 'V3/mV', 'V4/mV', 'V_H/mV']
HEAD_M = ['I_M/mA', 'V1/mV', 'V2/mV', 'V3/mV', 'V4/mV', 'V_H/mV']
HEAD_B = ['I_M/mA', 'B1/mT', 'B2/mT', 'B3/mT', 'B4/mT', 'B/mT']


def b_field(im_ma):
    """电磁铁磁感应强度（mT），I_M 以 mA 计，带轻微饱和。"""
    return 0.95 * im_ma * (1.0 - 0.06 * (im_ma / 500.0) ** 2)


def v_hall(i_s_ma, b_mT):
    """霍尔电压真值（mV）。"""
    return K_H_TRUE * i_s_ma * b_mT / 1000.0


def readings(vh, b_mT, i, scale):
    """把霍尔电压拆成四组换向读数（含各项副效应）。"""
    vh = vh + _noise(i, scale)
    ve = 0.02 * vh
    vn = 4.0e-4 * b_mT
    vrl = 3.0e-4 * b_mT
    v0 = 0.03
    v1 = round(vh + ve + vn + vrl + v0, 2)
    v2 = round(-vh - ve - vn - vrl - v0, 2)
    v3 = round(vh + ve - vn - vrl - v0, 2)
    v4 = round(-vh - ve + vn + vrl - v0, 2)
    return [v1, v2, v3, v4]


def _noise(i, scale):
    """确定性的小起伏，避免随机数。"""
    return scale * (math.sin(i * 1.73 + 0.4) * 0.7 + math.cos(i * 0.91) * 0.3)


def _fmt(v):
    return '−%.2f' % abs(v) if v < 0 else '%.2f' % v


def _bump(s, delta):
    """把某一格按 delta 微调，模拟末位抄错。"""
    v = float(s.replace('−', '-')) + delta
    s2 = '%.2f' % v
    return s2.replace('-', '−')


def _table_v(header, xs, fixed_im=None, fixed_is=None, phase=0):
    cells = [header]
    for i, x in enumerate(xs):
        if fixed_im is not None:
            b = b_field(fixed_im)
            vh = v_hall(x, b)
        else:
            b = b_field(x)
            vh = v_hall(fixed_is, b)
        vs = readings(vh, b, i + phase, 0.010 if fixed_im is not None else 0.008)
        vh_meas = (vs[0] - vs[1] + vs[2] - vs[3]) / 4.0
        cells.append([('%.2f' % x) if fixed_im is not None else str(x)]
                     + [_fmt(v) for v in vs] + ['%.3f' % vh_meas])
    return cells


def _table_b(im_xs):
    cells = [HEAD_B]
    for x in im_xs:
        b = b_field(x)
        cells.append([str(x), '%.1f' % b, '%.1f' % b, _fmt(-b), _fmt(-b), '%.1f' % b])
    return cells


def _table_u(i_xs):
    cells = [['I/mA', 'U_AC/mV']]
    for i, x in enumerate(i_xs):
        u = U_PER_MA * x * 1000.0 / 1000.0     # mV
        u += _noise(i + 3, 0.02)
        cells.append(['%.2f' % x, '%.2f' % u])
    return cells


def mock(ed):
    t1 = _table_v(HEAD_V, I_S_T1, fixed_im=300)
    t2 = _table_v(HEAD_M, IM_T2, fixed_is=1.00, phase=5)
    t3 = _table_b(IM_T3)
    t4 = _table_u(I_S_T1)
    notes = []

    # 错点 1：表 1 中 I_s = 2.50 mA 那一行 V₂ 末位抄错
    i = I_S_T1.index(2.50)
    raw = t1[i + 1][2]
    wrong = _bump(raw, 0.02)
    t1[i + 1][2] = wrong
    notes.append({
        'table': 't1', 'row': i + 1, 'col': 2,
        'where': '表1 · I_s = 2.50 mA · V₂ 那一格',
        'current': wrong, 'candidates': [raw],
        'why': 'V₂ 应与同一行 V₁ 的绝对值接近（两者只差换向），这一格末位疑似看错',
    })

    # 错点 2：表 3 中 I_M = 250 mA 那一行 B₃ 漏写负号
    j = IM_T3.index(250)
    v3 = t3[j + 1][3]
    t3[j + 1][3] = v3.lstrip('−')
    notes.append({
        'table': 't3', 'row': j + 1, 'col': 3,
        'where': '表3 · I_M = 250 mA · B₃ 那一格',
        'current': t3[j + 1][3], 'candidates': [v3],
        'why': 'B₃ 对应 −I_M、−I_s，毫特计读数应取负值，此格漏写了负号（会使该行 B 明显偏小）',
    })

    # 注入错值后重算 V_H、B 两列，保持表内自洽
    for cells in (t1, t2):
        for r in cells[1:]:
            vs = [float(str(v).replace('−', '-')) for v in r[1:5]]
            r[5] = '%.3f' % ((vs[0] - vs[1] + vs[2] - vs[3]) / 4.0)
    for r in t3[1:]:
        bs = [float(str(v).replace('−', '-')) for v in r[1:5]]
        r[5] = '%.1f' % ((bs[0] + bs[1] - bs[2] - bs[3]) / 4.0)

    return {
        'exp_id': ed['id'],
        'tables': {'t1': {'cells': t1}, 't2': {'cells': t2},
                   't3': {'cells': t3}, 't4': {'cells': t4}},
        'notes': notes,
        'provenance': {'source': 'mock', 'generator': 'mock_hall.py'},
    }
