# -*- coding: utf-8 -*-
"""液体表面张力系数测定：定标（逐差法）＋ 拉脱法测力 → α 与不确定度。

数据来自 data['tables']：
  t1 力敏传感器定标表（砝码质量 / 增重读数 / 减重读数 …）
  t2 拉脱读数表（U₁′、U₂′、ΔU_i，末行水温）
  t3 吊环内、外直径表（末行游标卡尺零点读数）

只依赖标准库；温度 → 公认值的换算查讲稿第 6 页的附录一。
"""

import math

G_DEFAULT = 9.794
ACC_DEFAULT = 7.244e-02            # 22.0 ℃ 水的表面张力系数（附录一）

# 讲稿附录一：温度 ℃ → σ /(10⁻³ N·m⁻¹)
APPENDIX = [
    (0, 75.62), (5, 74.90), (6, 74.76), (8, 74.48), (10, 74.20), (11, 74.07),
    (12, 73.92), (13, 73.78), (14, 73.64), (15, 73.48), (16, 73.34), (17, 73.20),
    (18, 73.05), (19, 72.89), (20, 72.75), (21, 72.60), (22, 72.44), (23, 72.28),
    (24, 72.12), (25, 71.96), (30, 71.15), (40, 69.55), (50, 67.90), (60, 66.17),
    (70, 64.41), (80, 62.60), (90, 60.74), (100, 58.84),
]

U_VOLT_MV = 0.01                   # 数字电压表分辨力
U_CAL_MM = 0.02                    # 游标卡尺分度值
U_MASS_REL = 0.05 / 1000.0 / math.sqrt(3.0)   # 砝码允差 0.05 mg / 1000 mg
U_G_REL = 2.0e-4                   # 本地重力加速度取值的相对不确定度


def _num(x):
    if x is None:
        return None
    s = str(x).strip()
    for a, b in (('−', '-'), ('–', '-'), ('—', '-'), ('－', '-'), ('，', ''),
                 (',', ''), ('（', ''), ('）', ''), ('(', ''), (')', '')):
        s = s.replace(a, b)
    try:
        return float(s)
    except ValueError:
        return None


def _mean(v):
    return sum(v) / float(len(v))


def _sd(v):
    n = len(v)
    if n < 2:
        return 0.0
    m = _mean(v)
    return math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1.0))


def _median(v):
    s = sorted(v)
    n = len(s)
    if n % 2:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2.0


def _sigma(t):
    """按附录一线性内插，返回某温度下水的表面张力系数（N/m）。"""
    if t is None:
        return None
    pts = sorted(APPENDIX)
    if t <= pts[0][0]:
        return pts[0][1] * 1e-3
    if t >= pts[-1][0]:
        return pts[-1][1] * 1e-3
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t0 <= t <= t1:
            return (v0 + (v1 - v0) * (t - t0) / (t1 - t0)) * 1e-3
    return None


def _cells(data, tid):
    tab = (data.get('tables') or {}).get(tid) or {}
    return tab.get('cells') or []


def _read_cal(cells):
    masses, ups, downs = [], [], []
    for r in cells[1:]:
        if not r:
            continue
        m = _num(r[0])
        if m is None or len(r) < 3:
            continue
        a, b = _num(r[1]), _num(r[2])
        if a is None or b is None:
            continue
        masses.append(m)
        ups.append(a)
        downs.append(b)
    if len(masses) < 5:
        raise ValueError('定标表不足 5 个质量台阶，无法用逐差法求 K')
    order = sorted(range(len(masses)), key=lambda i: masses[i])
    return ([masses[i] for i in order], [(ups[i] + downs[i]) / 2.0 for i in order],
            [ups[i] for i in order], [downs[i] for i in order])


def _read_pull(cells):
    u1s, u2s, dUs, water = [], [], [], None
    for r in cells[1:]:
        if not r:
            continue
        c0 = str(r[0]).strip()
        if '水温' in c0 or '室温' in c0:
            if len(r) > 1:
                water = _num(r[1])
            continue
        if _num(r[0]) is None:
            continue
        a = _num(r[1]) if len(r) > 1 else None
        b = _num(r[2]) if len(r) > 2 else None
        dv = _num(r[3]) if len(r) > 3 else None
        if a is not None and b is not None:
            u1s.append(a)
            u2s.append(b)
            dUs.append(a - b)
        elif dv is not None:
            u1s.append(None)
            u2s.append(None)
            dUs.append(dv)
    if not dUs:
        raise ValueError('拉脱读数表为空')
    return u1s, u2s, dUs, water


def _read_ring(cells):
    head = cells[0] if cells else []
    drop_last = bool(head) and '平均' in str(head[-1])   # 最后一列是平均值，别重复计入
    d1, d2, zero = [], [], 0.0
    for r in cells[1:]:
        if not r:
            continue
        c0 = str(r[0]).strip()
        vals = list(r[1:])
        if drop_last and len(vals) > 1:
            vals = vals[:-1]
        nums = [x for x in (_num(c) for c in vals) if x is not None]
        if '零点' in c0:
            if nums:
                zero = nums[0]
            continue
        if '内径' in c0 or ('D' in c0 and '1' in c0):
            if nums:
                d1 = nums
        elif '外径' in c0 or ('D' in c0 and '2' in c0):
            if nums:
                d2 = nums
    if not d1 or not d2:
        raise ValueError('表 3 缺少吊环内径或外径数据')
    return d1, d2, zero


def calc(ed, data, lsq):
    g = float(ed.get('g', G_DEFAULT))
    ms, us, ups, downs = _read_cal(_cells(data, 't1'))
    u1s, u2s, dUs, water = _read_pull(_cells(data, 't2'))
    d1s, d2s, zero = _read_ring(_cells(data, 't3'))

    # ---- 定标：逐差法跨 4 个台阶求 K -------------------------------------
    n_cal = len(ms)
    dU_list, K_list, pairs = [], [], []
    for i in range(n_cal):
        j = i - 4
        if j < 0:
            continue
        dv = us[i] - us[j]
        dm = (ms[i] - ms[j]) * 1e-6
        dU_list.append(dv)
        K_list.append(dm * g / dv)
        pairs.append((i, j))
    if not K_list:
        raise ValueError('定标表不足 5 个质量台阶，无法逐差')
    dU_row = [None] * n_cal
    K_row = [None] * n_cal
    for (i, j), dv, kv in zip(pairs, dU_list, K_list):
        dU_row[i] = dv
        K_row[i] = kv

    K = _mean(K_list)
    uA_K = _sd(K_list) / math.sqrt(len(K_list))
    dU_cal_mean = _mean(dU_list)
    uB_dU_cal = math.sqrt(2.0) * (U_VOLT_MV / 2.0 / math.sqrt(3.0))
    uB_K_rel = math.sqrt((uB_dU_cal / abs(dU_cal_mean)) ** 2 + U_MASS_REL ** 2
                         + U_G_REL ** 2)
    uK_rel = math.sqrt((uA_K / K) ** 2 + uB_K_rel ** 2)
    uK = K * uK_rel

    # ---- 拉脱读数 ---------------------------------------------------------
    n_u = len(dUs)
    dU_bar = _mean(dUs)
    uA_dU = _sd(dUs) / math.sqrt(n_u)
    uB_dU = math.sqrt(2.0) * (U_VOLT_MV / 2.0 / math.sqrt(3.0)) / math.sqrt(n_u)
    u_dU = math.sqrt(uA_dU ** 2 + uB_dU ** 2)
    rel_dU = u_dU / abs(dU_bar)

    # ---- 吊环直径 ---------------------------------------------------------
    D1 = _mean(d1s) - zero
    D2 = _mean(d2s) - zero
    Dsum = D1 + D2
    uA_D = math.sqrt(_sd(d1s) ** 2 / len(d1s) + _sd(d2s) ** 2 / len(d2s))
    uB_one = U_CAL_MM / 2.0 / math.sqrt(3.0)
    uB_D = math.sqrt((uB_one / math.sqrt(len(d1s))) ** 2
                     + (uB_one / math.sqrt(len(d2s))) ** 2 + uB_one ** 2)
    u_D = math.sqrt(uA_D ** 2 + uB_D ** 2)
    rel_D = u_D / Dsum

    # ---- α 与不确定度 -----------------------------------------------------
    alpha = K * dU_bar / (math.pi * Dsum * 1e-3)
    accepted = _sigma(water)
    if not accepted:
        accepted = float(ed.get('accepted') or ACC_DEFAULT)
    comp = {'K': uK / K, 'U': rel_dU, 'D': rel_D}
    rel_u = math.sqrt(sum(v ** 2 for v in comp.values()))
    u_alpha = alpha * rel_u
    rel_err = (alpha - accepted) / accepted * 100.0
    n_sigma = abs(rel_err) / 100.0 / rel_u if rel_u else 0.0

    # 偏离最大的一次拉脱读数（疑为峰值抢读），剔除后作对照
    idx = max(range(n_u), key=lambda i: abs(dUs[i] - dU_bar))
    rest = [dUs[i] for i in range(n_u) if i != idx]
    dU_excl = _mean(rest) if rest else dU_bar
    alpha_excl = K * dU_excl / (math.pi * Dsum * 1e-3)
    rel_err_excl = (alpha_excl - accepted) / accepted * 100.0

    # 内径用中位数（避开卡倒角的那一次）后的对照值
    D1_fix = _median(d1s) - zero
    alpha_Dfix = K * dU_bar / (math.pi * (D1_fix + D2) * 1e-3)

    return {
        't1': {'n': n_cal, 'mass_mg': ms, 'u_up': ups, 'u_down': downs,
               'u_mean': us, 'dU_mV': dU_row, 'K': K_row, 'K_mean': K,
               'u_K': uK, 'uA_K_rel': uA_K / K, 'uB_K_rel': uB_K_rel,
               'dU_cal_mean': dU_cal_mean, 'g': g},
        't2': {'n': n_u, 'u1_mV': u1s, 'u2_mV': u2s, 'dU_mV': dUs,
               'dU_mean': dU_bar, 'u_dU': u_dU, 'water_C': water},
        't3': {'D1_mm': D1, 'D2_mm': D2, 'Dsum_mm': Dsum, 'D1_list': d1s,
               'D2_list': d2s, 'zero_mm': zero, 'u_D_mm': u_D,
               'D1_median_mm': D1_fix},
        'result': {'alpha': alpha, 'u_alpha': u_alpha, 'rel_u': rel_u,
                   'accepted': accepted, 'rel_err_pct': rel_err,
                   'n_sigma': n_sigma, 'K': K, 'u_K': uK, 'K_list': K_list,
                   'dU_list': dU_list, 'dU_mean': dU_bar, 'components': comp,
                   'alpha_excl': alpha_excl, 'rel_err_excl': rel_err_excl,
                   'dU_excl': dU_excl, 'excl_index': idx + 1,
                   'alpha_Dfix': alpha_Dfix, 'D1_median_mm': D1_fix,
                   'water_C': water, 'accepted_C': 22.0},
        'provenance': data.get('provenance', {}),
    }
