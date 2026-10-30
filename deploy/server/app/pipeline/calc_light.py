# -*- coding: utf-8 -*-
"""光速测定：从等间距法与等相位法的记录表求调制波波长与空气中的光速。

表 1（等间距法）每列是一个反射镜位置 x，给出 D = x_i − x_0、示波器上波形相移
格数 r 与相移量 φ；由 φ = 2πr/5、λ = 2π·2D/φ 得 λ_i，取平均后 c = λf。
表 2（等相位法）每次把反射镜移到 72° 相位点，并拉回 0° 复测 X_0′，
用 X̄_0 = (X_0 + X_0′)/2、D = X_i − X̄_0 同样算 λ 与 c。

只用标准库；lsq 由 core 注入（这里不拟合直线，保留参数以统一签名）。
"""

import math
import re

F_HZ = 100e6        # 载波频率 100 MHz
R0 = 5.0            # 一个周期在示波器上占 5 大格
C_TRUE = 2.998e8    # 光速公认值


def _num(x):
    """把 '12.34'、'−0.05'、'45.00 cm' 之类统一成 float，读不出返回 None。"""
    if x is None or isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if not s:
        return None
    for ch in ('\u2212', '\u2013', '\u2014', '\u2015'):
        s = s.replace(ch, '-')
    s = s.replace(' ', '').replace('\u3000', '').replace('，', '')
    try:
        return float(s)
    except ValueError:
        pass
    m = re.search(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', s)
    return float(m.group()) if m else None


def _cells(data, tid):
    """兼容 data['tables'][tid]['cells'] 与 data[tid]['cells'] 两种形态。"""
    tabs = data.get('tables') if isinstance(data, dict) else None
    t = None
    if isinstance(tabs, dict):
        t = tabs.get(tid)
    if t is None and isinstance(data, dict):
        t = data.get(tid)
    if t is None:
        return []
    if isinstance(t, dict):
        return t.get('cells') or []
    if isinstance(t, (list, tuple)):
        return list(t)
    return []


def _rows(cells):
    out = []
    for row in cells or []:
        if isinstance(row, (list, tuple)):
            out.append([('' if c is None else str(c).strip()) for c in row])
    return out


def _find(rows, pred):
    for i, row in enumerate(rows):
        if row and pred(row[0].lower()):
            return i
    return None


def _vals(rows, i, n):
    if i is None or not rows:
        return [None] * n
    row = rows[i]
    out = []
    for j in range(1, n + 1):
        out.append(_num(row[j]) if j < len(row) else None)
    return out


def _lam(D_cm, r, r0):
    """λ = 2π·2D/φ，φ = 2πr/r0，故 λ = 2D·r0/r（D 用 m，r 用格）。"""
    return 2.0 * (D_cm / 100.0) * r0 / r if r else None


def _mean(v):
    return sum(v) / float(len(v)) if v else 0.0


def _u_mean(v):
    """平均值的标准偏差 u = s/√n（s 为样本标准偏差）。"""
    n = len(v)
    if n < 2:
        return 0.0
    m = _mean(v)
    s = math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1.0))
    return s / math.sqrt(n)


def calc(ed, data, lsq):
    f = float((ed or {}).get('f_hz') or F_HZ)
    r0 = float((ed or {}).get('r0_divisions') or R0)

    # ---------------- 表 1：等间距法 ----------------
    rows1 = _rows(_cells(data, 't1'))
    if not rows1:
        raise ValueError('记录表里找不到表 1（等间距法）')
    n1 = max(len(r) for r in rows1) - 1

    ix = _find(rows1, lambda s: '读数' in s)
    if ix is None:
        ix = _find(rows1, lambda s: '位置' in s)
    iD = _find(rows1, lambda s: s.startswith('d') or 'd_i' in s)
    ir = _find(rows1, lambda s: '格' in s)
    iphi = _find(rows1, lambda s: 'φ' in s and 'λ' not in s)
    ilam = _find(rows1, lambda s: ('λ' in s or '波长' in s)
                 and '平均' not in s and '̄' not in s)
    imean = _find(rows1, lambda s: '平均' in s or '̄' in s)

    xs = _vals(rows1, ix, n1)
    Ds = _vals(rows1, iD, n1)
    rs = _vals(rows1, ir, n1)
    phis = _vals(rows1, iphi, n1)
    lams = _vals(rows1, ilam, n1)
    if xs[0] is None or Ds[0] is None:
        raise ValueError('表 1 缺少 x_i 或 D_i 行')

    # 逐点由 D、r 重算 φ 与 λ（学生抄录值仅用于核对）
    lam_calc, phi_calc, used = [], [], []
    for j in range(n1):
        d, r = Ds[j], rs[j]
        if d is None or not r:
            continue
        used.append(j)
        phi_calc.append(2.0 * math.pi * r / r0)
        lam_calc.append(_lam(d, r, r0))
    if len(lam_calc) < 2:
        raise ValueError('表 1 有效测点不足（%d 个）' % len(lam_calc))
    lam1 = _mean(lam_calc)
    u_lam1 = _u_mean(lam_calc)
    c1 = lam1 * f
    rel1 = (c1 - C_TRUE) / C_TRUE * 100.0

    # 学生把 D 抄错时，用 x_i − x_0 重算的对照值
    d_check = []
    for j in range(n1):
        if xs[j] is None or Ds[j] is None:
            continue
        d_check.append((xs[j] - xs[0]) - Ds[j])
    d_check_max = max((abs(v) for v in d_check), default=0.0)
    lam1_fix = _mean([_lam(xs[j] - xs[0], rs[j], r0) for j in used])
    c1_fix = lam1_fix * f

    phi_check_max = 0.0
    for k, j in enumerate(used):
        if j < len(phis) and phis[j] is not None:
            phi_check_max = max(phi_check_max, abs(phis[j] - phi_calc[k]))
    lam_check_max = 0.0
    for k, j in enumerate(used):
        if j < len(lams) and lams[j] is not None:
            lam_check_max = max(lam_check_max, abs(lams[j] - lam_calc[k]))

    # ---------------- 表 2：等相位法 ----------------
    rows2 = _rows(_cells(data, 't2'))
    if not rows2:
        raise ValueError('记录表里找不到表 2（等相位法）')
    n2 = max(len(r) for r in rows2) - 1

    ip2 = _find(rows2, lambda s: 'φ' in s)
    iX0 = _find(rows2, lambda s: s.startswith('x_0') and '′' not in s and '̄' not in s)
    iXi = _find(rows2, lambda s: s.startswith('x_i') or s.startswith('xi'))
    iX0p = _find(rows2, lambda s: '′' in s or "'" in s)
    iXb = _find(rows2, lambda s: '̄' in s or '平均' in s)
    iD2 = _find(rows2, lambda s: s.startswith('d'))
    iL2 = _find(rows2, lambda s: ('λ' in s or '波长' in s)
                and '平均' not in s and '̄' not in s)

    phis2 = _vals(rows2, ip2, n2)
    X0 = _vals(rows2, iX0, n2)
    Xi = _vals(rows2, iXi, n2)
    X0p = _vals(rows2, iX0p, n2)
    Xb = _vals(rows2, iXb, n2)
    D2 = _vals(rows2, iD2, n2)
    lam2_rec = _vals(rows2, iL2, n2)

    lam2, lam2_fix, Xb_fix, used2 = [], [], [], []
    for j in range(n2):
        x0, xi, x0p = X0[j], Xi[j], X0p[j]
        if x0 is None or xi is None:
            continue
        xb = (x0 + x0p) / 2.0 if x0p is not None else (Xb[j] if Xb[j] is not None else x0)
        d = D2[j] if D2[j] is not None else xi - xb
        deg = phis2[j] if phis2[j] is not None else 72.0
        phi = math.radians(deg)
        used2.append(j)
        Xb_fix.append(xb)
        lam2.append(4.0 * math.pi * (d / 100.0) / phi)
        # 复测 0° 两个读数相差超过 5 mm，讲义要求重测；这里用 X_0 代替 X_0′ 作对照
        if x0p is not None and abs(x0p - x0) > 0.5:
            xb_fix = x0
        else:
            xb_fix = xb
        lam2_fix.append(4.0 * math.pi * ((xi - xb_fix) / 100.0) / phi)
    if not lam2:
        raise ValueError('表 2 有效测点不足')
    lam2_mean = _mean(lam2)
    u_lam2 = _u_mean(lam2)
    c2 = lam2_mean * f
    rel2 = (c2 - C_TRUE) / C_TRUE * 100.0
    c2_fix = _mean(lam2_fix) * f

    x0p_diff = max((abs(X0p[j] - X0[j]) for j in used2
                    if X0p[j] is not None and X0[j] is not None), default=0.0)

    t1 = {'x': xs, 'D': Ds, 'r': rs, 'phi': phis, 'lam': lams,
          'lam_calc': lam_calc, 'mean': lam1, 'mean_fix': lam1_fix,
          'r0': r0, 'n': len(used)}
    t2 = {'phi_deg': phis2, 'X0': X0, 'Xi': Xi, 'X0p': X0p, 'Xbar': Xb,
          'D': D2, 'lam': lam2_rec, 'lam_calc': lam2, 'mean': lam2_mean,
          'mean_fix': _mean(lam2_fix), 'Xbar_fix': Xb_fix, 'n': len(used2)}

    result = {
        'c_1e8': c1 / 1e8,
        'rel_err_pct': rel1,
        'u_c_1e8': u_lam1 * f / 1e8,
        'c_2e8': c2 / 1e8,
        'rel_err_2_pct': rel2,
        'u_c_2e8': u_lam2 * f / 1e8,
        'lam1': lam1,
        'lam2': lam2_mean,
        'lam1_fix': lam1_fix,
        'c1_fix_1e8': c1_fix / 1e8,
        'lam2_fix': _mean(lam2_fix),
        'c2_fix_1e8': c2_fix / 1e8,
        'u_lam1': u_lam1,
        'u_lam2': u_lam2,
        'f_mhz': f / 1e6,
        'r0': r0,
        'c_true_1e8': C_TRUE / 1e8,
        'n1': len(lam_calc),
        'n2': len(lam2),
        'd_check_max': d_check_max,
        'd_check': d_check,
        'phi_check_max': phi_check_max,
        'lam_check_max': lam_check_max,
        'x0p_diff_max': x0p_diff,
        'two_method_diff_pct': abs(c1 - c2) / ((c1 + c2) / 2.0) * 100.0,
    }

    return {'t1': t1, 't2': t2, 'result': result,
            'provenance': data.get('provenance') or {'source': 'mock'}}
