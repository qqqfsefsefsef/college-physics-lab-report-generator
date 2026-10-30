# -*- coding: utf-8 -*-
"""用霍尔效应测磁场（实验 31）的确定性计算。

表结构（桩数据 / 识别结果 / 用户手填都用这一套）：
  t1  线圈 1 单独通电：['x/mm','V1/mV','V2/mV','V3/mV','V4/mV','V_H/mV','B/mT'] + 25 行数据
  t2  线圈 2 单独通电：同 t1
  t3  两线圈同向串联：同 t1

V1~V4 的换向组合与讲稿表 1~表 3 一致：
  V1 (+I_s,+I_M)   V2 (+I_s,−I_M)   V3 (−I_s,−I_M)   V4 (−I_s,+I_M)
对称测量法：V_H = (V1 − V2 + V3 − V4)/4，可消去能斯特效应、里吉—勒杜克效应与不等势电位。
霍尔灵敏度由表 3 中 x = 0 处的 V_H 按讲稿式(5) 标定：K_H = V_H0/(I_s·B0)，B0 取理论值 2.25 mT。
各点磁感应强度按讲稿式(6)：B = V_H/(K_H·I_s)。
"""
import math

MU0 = 4e-7 * math.pi
T_SINGLE_CENTER = 1.5708e-3   # μ0NI/(2R)，I=0.5 A、N=500、R=0.1 m，单位 T
T_HELM_CENTER = 2.25e-3       # 8μ0NI/(5^{3/2}R)，同上，单位 T
COIL1_MM = -50.0              # 两线圈间距等于半径时，线圈 1 中心在 x = −R/2
COIL2_MM = 50.0               # 线圈 2 中心在 x = +R/2


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


def _rows(cells):
    """把 cells 解析成 [[x, V1, V2, V3, V4], ...]，按 x 升序；表头/空行自动跳过。"""
    out = []
    for r in cells or []:
        if not r or len(r) < 5:
            continue
        vals = [_num(v) for v in r[:5]]
        if any(math.isnan(v) for v in vals):
            continue
        out.append(vals)
    out.sort(key=lambda v: v[0])
    return out


def _v_h(vals):
    """对称测量法：V_H = (V1 − V2 + V3 − V4)/4（mV）。"""
    return (vals[1] - vals[2] + vals[3] - vals[4]) / 4.0


def _theory_single(x_mm):
    x = x_mm / 1000.0
    r = 0.100
    return MU0 * 500 * 0.500 * r * r / (2.0 * (r * r + x * x) ** 1.5)


def _theory_helm(z_mm):
    z = z_mm / 1000.0
    r = 0.100
    a = (r * r + (r / 2.0 + z) ** 2) ** 1.5
    b = (r * r + (r / 2.0 - z) ** 2) ** 1.5
    return 0.5 * MU0 * 500 * 0.500 * r * r * (1.0 / a + 1.0 / b)


def calc(ed, data, lsq):
    cond = ed.get('conditions') or {}
    i_s = float(cond.get('I_s_mA', 5.0))
    b0 = float(cond.get('B0_theory_mT', 2.25)) * 1e-3

    t1 = _rows((data.get('t1') or {}).get('cells'))
    t2 = _rows((data.get('t2') or {}).get('cells'))
    t3 = _rows((data.get('t3') or {}).get('cells'))

    vh1 = [_v_h(r) for r in t1]
    vh2 = [_v_h(r) for r in t2]
    vh3 = [_v_h(r) for r in t3]

    # ---- 霍尔灵敏度：表 3 中 x = 0 处按式(5) 标定
    k_h = float('nan')
    vh0 = float('nan')
    if t3:
        k = min(range(len(t3)), key=lambda i: abs(t3[i][0]))
        vh0 = vh3[k]
        if abs(vh0) > 0 and i_s > 0:
            k_h = abs(vh0) / (i_s * b0)          # mV/(mA·T)

    def b_of(vh):
        return vh / (k_h * i_s) * 1e3 if k_h and not math.isnan(k_h) else float('nan')

    b1 = [b_of(v) for v in vh1]
    b2 = [b_of(v) for v in vh2]
    br = [b_of(v) for v in vh3]

    def center(rows, bs):
        if not rows:
            return float('nan')
        i = min(range(len(rows)), key=lambda j: abs(rows[j][0]))
        return bs[i]

    b1_0, b2_0, br_0 = center(t1, b1), center(t2, b2), center(t3, br)

    # ---- 叠加关系：B(1)+B(2) 与 B(R) 比较
    sup = []
    n = min(len(t1), len(t2), len(t3))
    for i in range(n):
        if abs(t1[i][0] - t2[i][0]) > 0.5 or abs(t1[i][0] - t3[i][0]) > 0.5:
            continue
        s = b1[i] + b2[i]
        dev = (s - br[i]) / br[i] * 100.0 if br[i] else float('nan')
        sup.append((t1[i][0], s, dev))
    sup_c = [(x, s, d) for x, s, d in sup if abs(x) <= 80.0]
    sup_dev = max(abs(d) for _, _, d in sup_c) if sup_c else float('nan')
    sup_center = next((d for x, _, d in sup if abs(x) < 0.5), float('nan'))

    # ---- 叠加曲线的线性：以 B(1)+B(2) 为横轴、B(R) 为纵轴作直线
    fit = {}
    if len(sup) >= 3:
        xs = [s for _, s, _ in sup]
        ys = []
        for x, _, _ in sup:
            j = min(range(len(t3)), key=lambda k: abs(t3[k][0] - x))
            ys.append(br[j])
        fit = lsq(xs, ys)

    rel_center = (br_0 - b0 * 1e3) / (b0 * 1e3) * 100.0 if br_0 == br_0 else float('nan')

    # ---- 单线圈中心读数：峰值出现在各自线圈中心处（x = ∓R/2），与 μ0NI/(2R) 比较
    def peak(rows, bs):
        if not rows:
            return float('nan'), float('nan')
        i = max(range(len(rows)), key=lambda j: abs(bs[j]) if bs[j] == bs[j] else -1.0)
        return bs[i], rows[i][0]

    b1_max, b1_max_x = peak(t1, b1)
    b2_max, b2_max_x = peak(t2, b2)
    bmax_avg = 0.5 * (b1_max + b2_max) if (b1_max == b1_max and b2_max == b2_max) else float('nan')
    rel_single = (bmax_avg - T_SINGLE_CENTER * 1e3) / (T_SINGLE_CENTER * 1e3) * 100.0 \
        if bmax_avg == bmax_avg else float('nan')

    th1 = [_theory_single(x - COIL1_MM) * 1e3 for x in [r[0] for r in t1]]
    th2 = [_theory_single(x - COIL2_MM) * 1e3 for x in [r[0] for r in t2]]
    th3 = [_theory_helm(x) * 1e3 for x in [r[0] for r in t3]]

    return {
        't1': {'x': [r[0] for r in t1], 'v': [r[1:5] for r in t1], 'vh': vh1, 'b': b1},
        't2': {'x': [r[0] for r in t2], 'v': [r[1:5] for r in t2], 'vh': vh2, 'b': b2},
        't3': {'x': [r[0] for r in t3], 'v': [r[1:5] for r in t3], 'vh': vh3, 'b': br},
        'theory': {'single1': th1, 'single2': th2, 'helm': th3},
        'result': {
            'K_H': k_h,
            'V_H0_mV': vh0,
            'B0_theory_mT': b0 * 1e3,
            'B1_0_mT': b1_0,
            'B2_0_mT': b2_0,
            'B_R0_mT': br_0,
            'B_sum0_mT': b1_0 + b2_0,
            'B1_max_mT': b1_max,
            'B2_max_mT': b2_max,
            'B1_max_x_mm': b1_max_x,
            'B2_max_x_mm': b2_max_x,
            'B_single_theory_mT': T_SINGLE_CENTER * 1e3,
            'sum_slope': fit.get('slope'),
            'sum_r2': fit.get('r2'),
            'rel_dev_center_pct': rel_center,
            'sup_dev_center_pct': sup_center,
            'sup_dev_pct': sup_dev,
            'rel_single_center_pct': rel_single,
            'n_points': n,
        },
        'provenance': data.get('provenance', {}),
    }
