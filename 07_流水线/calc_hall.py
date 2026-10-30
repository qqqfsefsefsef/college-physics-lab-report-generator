# -*- coding: utf-8 -*-
"""霍尔效应及其应用（实验 30）的确定性计算。

表结构（桩数据 / 识别结果 / 用户手填都用这一套）：
  t1  ['I_s/mA','V1/mV','V2/mV','V3/mV','V4/mV','V_H/mV'] + 6 行（I_M = 300 mA）
  t2  ['I_M/mA','V1/mV','V2/mV','V3/mV','V4/mV','V_H/mV'] + 10 行（I_s = 1.00 mA）
  t3  ['I_M/mA','B1/mT','B2/mT','B3/mT','B4/mT','B/mT'] + 10 行（I_s = 1.00 mA）
  t4  ['I/mA','U_AC/mV'] + 6 行（电导率测量，五端引线中的 A、C 两电极）

换向组合与讲稿表 1~表 3 一致：
  V1 (+I_M,+I_s)   V2 (+I_M,−I_s)   V3 (−I_M,−I_s)   V4 (−I_M,+I_s)
对称测量法：V_H = (V1 − V2 + V3 − V4)/4，消去能斯特、里吉—勒杜克与不等势电位；
B 表的平均式按讲稿：B = (B1 + B2 − B3 − B4)/4（B3、B4 以负值记录时即为算术平均）。
"""
import math

E_CHARGE = 1.602e-19
D_DEFAULT = 2.0e-4      # 霍尔元件厚度（m）
L_DEFAULT = 1.5e-3      # 电导率测量中 A、C 之间的距离（m）
B_WIDTH = 1.5e-3        # 霍尔元件宽度（m）


def _num(x):
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace('−', '-').replace('–', '-').replace(' ', '')
    if not s:
        return float('nan')
    try:
        return float(s)
    except ValueError:
        return float('nan')


def _rows(cells, need):
    """把 cells 解析成数值行；跳过表头、空行和不完整的行。"""
    out = []
    for r in cells or []:
        if not r or len(r) < need:
            continue
        vals = [_num(v) for v in r[:need]]
        if any(math.isnan(v) for v in vals):
            continue
        out.append(vals)
    return out


def _v_h(vals):
    """对称测量法：V_H = (V1 − V2 + V3 − V4)/4（mV）。"""
    return (vals[1] - vals[2] + vals[3] - vals[4]) / 4.0


def _b_avg(vals):
    """B 的平均式：B = (B1 + B2 − B3 − B4)/4（mT）。"""
    return (vals[1] + vals[2] - vals[3] - vals[4]) / 4.0


def calc(ed, data, lsq):
    cond = ed.get('conditions') or {}
    i_s_t2 = float(cond.get('I_s_mA_table1', 1.0))
    d = float(cond.get('d_m', D_DEFAULT))
    l_len = float(cond.get('l_m', L_DEFAULT))
    b_w = float(cond.get('b_m', B_WIDTH))

    t1 = _rows((data.get('t1') or {}).get('cells'), 5)
    t2 = _rows((data.get('t2') or {}).get('cells'), 5)
    t3 = _rows((data.get('t3') or {}).get('cells'), 5)
    t4 = _rows((data.get('t4') or {}).get('cells'), 2)

    is_1 = [r[0] for r in t1]
    vh_1 = [_v_h(r) for r in t1]
    im_2 = [r[0] for r in t2]
    vh_2 = [_v_h(r) for r in t2]
    im_3 = [r[0] for r in t3]
    b_3 = [_b_avg(r) for r in t3]
    i_4 = [r[0] for r in t4]
    u_4 = [r[1] for r in t4]

    # ---- 线性拟合
    fit_s = lsq(is_1, vh_1) if len(is_1) >= 3 else {}
    fit_m = lsq(im_2, vh_2) if len(im_2) >= 3 else {}
    fit_b = lsq(im_3, b_3) if len(im_3) >= 3 else {}
    fit_u = lsq(i_4, u_4) if len(i_4) >= 3 else {}

    k_s = fit_s.get('slope', float('nan'))          # mV/mA
    k_m = fit_m.get('slope', float('nan'))          # mV/mA
    k_b = fit_b.get('slope', float('nan'))          # mT/mA
    r_s = fit_u.get('slope', float('nan'))          # mV/mA = Ω

    # ---- 固定励磁电流 300 mA 处的磁感应强度（由表 3 拟合）
    im_ref = float(cond.get('I_M_mA_table1', 300.0))
    b_ref_mT = k_b * im_ref + fit_b.get('intercept', 0.0) if fit_b else float('nan')
    b_ref_T = b_ref_mT * 1e-3

    # ---- 霍尔系数与灵敏度：两条独立路径
    # 路径 1：表 1 的 V_H–I_s 斜率 k_s = R_H·B/d
    r_h_a = k_s * d / b_ref_T if b_ref_T and not math.isnan(b_ref_T) else float('nan')
    k_h_a = r_h_a / d if r_h_a == r_h_a else float('nan')
    # 路径 2：表 2 的 V_H–I_M 斜率 k_m 与表 3 的 B–I_M 斜率 k_b
    k_h_b = (k_m / i_s_t2) / (k_b * 1e-3) if k_b and k_b == k_b else float('nan')
    r_h_b = k_h_b * d if k_h_b == k_h_b else float('nan')

    r_h = 0.5 * (r_h_a + r_h_b) if (r_h_a == r_h_a and r_h_b == r_h_b) else r_h_a
    k_h = r_h / d if r_h == r_h else float('nan')

    # ---- 载流子浓度与迁移率
    n_m3 = 1.0 / (r_h * E_CHARGE) if r_h and r_h == r_h else float('nan')
    sigma = l_len / (b_w * d * r_s) if r_s and r_s == r_s else float('nan')
    mu = abs(r_h) * sigma if (r_h == r_h and sigma == sigma) else float('nan')

    # ---- 元件厚度/宽度/长度给出的几何面积
    s_cross = b_w * d

    return {
        't1': {'x': is_1, 'v': [r[1:5] for r in t1], 'vh': vh_1,
               'slope': k_s, 'r2': fit_s.get('r2'), 'intercept': fit_s.get('intercept')},
        't2': {'x': im_2, 'v': [r[1:5] for r in t2], 'vh': vh_2,
               'slope': k_m, 'r2': fit_m.get('r2'), 'intercept': fit_m.get('intercept')},
        't3': {'x': im_3, 'b': [r[1:5] for r in t3], 'b_avg': b_3,
               'slope': k_b, 'r2': fit_b.get('r2'), 'intercept': fit_b.get('intercept')},
        't4': {'x': i_4, 'u': u_4, 'r': r_s, 'r2': fit_u.get('r2')},
        'result': {
            'R_H': r_h, 'R_H_a': r_h_a, 'R_H_b': r_h_b,
            'K_H': k_h, 'K_H_a': k_h_a, 'K_H_b': k_h_b,
            'n_m3': n_m3, 'sigma_S_m': sigma, 'mu': mu,
            'R_sample_ohm': r_s, 'B_ref_mT': b_ref_mT,
            'k_s_mV_per_mA': k_s, 'k_m_mV_per_mA': k_m, 'k_b_mT_per_mA': k_b,
            'r2_s': fit_s.get('r2'), 'r2_m': fit_m.get('r2'), 'r2_b': fit_b.get('r2'),
            'r2_u': fit_u.get('r2'),
            'd_mm': d * 1e3, 'l_mm': l_len * 1e3, 'b_mm': b_w * 1e3,
            'S_m2': s_cross, 'n_points': len(t1),
        },
        'provenance': data.get('provenance', {}),
    }
