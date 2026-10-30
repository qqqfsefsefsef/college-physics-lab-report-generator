# -*- coding: utf-8 -*-
"""验证马吕斯定律：从记录表（转角 → 三次光功率）算归一化光强，
再对 Ī/I0 = f(cos²α) 作分象限线性拟合，给出斜率、截距、相关系数与平均偏差。

只用标准库；lsq 由 core 注入（core.lsq(xs, ys) → dict）。
"""

import math
import re


def _num(x):
    """把 '12.34'、'−0.05'、'0.020 mW' 之类统一成 float，读不出返回 None。"""
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


def _fit(lsq, xs, ys):
    if len(xs) < 2:
        return None
    try:
        return lsq(xs, ys)
    except Exception:
        return None


def calc(ed, data, lsq):
    rows = _rows(_cells(data, 't1'))

    # ---- 找角度行（第一列含「角」或 α，且右侧至少 5 个数）
    angle_i = None
    for i, row in enumerate(rows):
        if not row:
            continue
        label = row[0].lower()
        nnum = sum(1 for c in row[1:] if _num(c) is not None)
        if nnum >= 5 and ('角' in label or 'α' in label or 'alpha' in label):
            angle_i = i
            break
    best_n = 0
    if angle_i is None:
        best = None
        for i, row in enumerate(rows):
            nnum = sum(1 for c in row[1:] if _num(c) is not None)
            if nnum > best_n:
                best, best_n = i, nnum
        angle_i = best
    else:
        best_n = sum(1 for c in rows[angle_i][1:] if _num(c) is not None)
    if angle_i is None or best_n < 3:
        raise ValueError('记录表里找不到角度这一行')

    angle_cols, angles = [], []
    for j in range(1, len(rows[angle_i])):
        v = _num(rows[angle_i][j])
        if v is not None:
            angle_cols.append(j)
            angles.append(v)
    if len(angles) < 5:
        raise ValueError('角度这一行只有 %d 个数，凑不成一条曲线' % len(angles))

    # ---- 找 cos²α 行（第一列含 cos）
    cos_i = None
    for i, row in enumerate(rows):
        if row and 'cos' in row[0].lower():
            cos_i = i
            break

    # ---- 找各次光强读数行：标签以大写 I 开头、带单位斜杠、不属于 Ī 与归一化
    read_is = []
    for i, row in enumerate(rows):
        if i in (angle_i, cos_i) or not row:
            continue
        lab = row[0]
        low = lab.lower()
        nnum = sum(1 for c in row[1:] if _num(c) is not None)
        if nnum < 5:
            continue
        if 'cos' in low:
            continue
        if '平均' in lab or '均值' in lab or 'avg' in low:
            continue
        if lab[:1] == 'I' and not lab.startswith('Ī'):
            read_is.append(i)
    if not read_is:
        for i, row in enumerate(rows):
            if i in (angle_i, cos_i) or not row:
                continue
            lab = row[0]
            low = lab.lower()
            if '平均' in lab or '均值' in lab or 'i_0' in low or 'i0' in low:
                continue
            if '%' in lab or '归一' in lab:
                continue
            if sum(1 for c in row[1:] if _num(c) is not None) >= 5:
                read_is.append(i)
    read_is = read_is[:3]
    if not read_is:
        raise ValueError('记录表里找不到光功率读数行')

    reads = []
    for i in read_is:
        vals = []
        for j in angle_cols:
            vals.append(_num(rows[i][j]) if j < len(rows[i]) else None)
        reads.append(vals)

    # ---- 三次读数按角度取平均；I0 取 Ī 的最大值（讲义的规定）
    used, means = [], []
    for k in range(len(angles)):
        vals = [r[k] for r in reads if k < len(r) and r[k] is not None]
        if not vals:
            continue
        used.append(k)
        means.append(sum(vals) / float(len(vals)))
    if len(used) < 4:
        raise ValueError('有效测点不足（%d 个）' % len(used))
    i0 = max(means)

    ang = [angles[k] for k in used]
    cos2 = [math.cos(math.radians(a)) ** 2 for a in ang]
    norm = [m / i0 for m in means]

    # ---- 记录的 cos²α 与本报告重算值比较（学生偶尔会抄错这一行）
    cos_typo = 0.0
    if cos_i is not None:
        for k, j in enumerate(angle_cols):
            if k not in used or j >= len(rows[cos_i]):
                continue
            rec = _num(rows[cos_i][j])
            if rec is not None:
                cos_typo = max(cos_typo, abs(rec - math.cos(math.radians(angles[k])) ** 2))

    # ---- 分四个象限作 Ī/I0 — cos²α 线性拟合
    quads = []
    for name, span, lo, hi in (
            ('第一象限', '0°～90°', -1e-9, 90.0),
            ('第二象限', '90°～180°', 90.0, 180.0),
            ('第三象限', '180°～270°', 180.0, 270.0),
            ('第四象限', '270°～360°', 270.0, 360.0)):
        xs, ys = [], []
        for a, x, y in zip(ang, cos2, norm):
            inside = (a >= lo - 1e-9) and (a <= hi + 1e-9)
            if name != '第一象限':
                inside = (a > lo + 1e-9) and (a <= hi + 1e-9)
            if inside:
                xs.append(x)
                ys.append(y)
        f = _fit(lsq, xs, ys)
        if f:
            quads.append({'name': name, 'span': span, 'n': len(xs),
                          'k': f['slope'], 'b': f['intercept'], 'r': f['r'],
                          'u_k': f.get('se_slope') or 0.0})

    glob = _fit(lsq, cos2, norm) or {}

    if quads:
        k_mean = sum(q['k'] for q in quads) / len(quads)
        b_mean = sum(q['b'] for q in quads) / len(quads)
        r_mean = sum(q['r'] for q in quads) / len(quads)
        r_min = min(q['r'] for q in quads)
        u_k = math.sqrt(sum((q['u_k'] or 0.0) ** 2 for q in quads) / len(quads))
    else:
        k_mean = glob.get('slope', 0.0)
        b_mean = glob.get('intercept', 0.0)
        r_mean = glob.get('r', 0.0)
        r_min = r_mean
        u_k = glob.get('se_slope') or 0.0

    devs = [abs(y - x) for x, y in zip(cos2, norm)]
    dev_pct = sum(devs) / len(devs) * 100.0
    dev_max = max(devs)
    dev_max_angle = ang[devs.index(dev_max)]

    # ---- 稳健性检查：用三次读数的中位数代替平均值重算（不被单个笔误带偏）
    meds = []
    for k in used:
        vals = sorted(r[k] for r in reads if k < len(r) and r[k] is not None)
        meds.append(vals[len(vals) // 2] if len(vals) % 2 else
                    (vals[len(vals) // 2 - 1] + vals[len(vals) // 2]) / 2.0)
    m0 = max(meds)
    norm_m = [m / m0 for m in meds]
    quads_m = []
    for name, span, lo, hi in (
            ('第一象限', '0°～90°', -1e-9, 90.0),
            ('第二象限', '90°～180°', 90.0, 180.0),
            ('第三象限', '180°～270°', 180.0, 270.0),
            ('第四象限', '270°～360°', 270.0, 360.0)):
        xs, ys = [], []
        for a, x, y in zip(ang, cos2, norm_m):
            if name == '第一象限':
                inside = (a >= lo - 1e-9) and (a <= hi + 1e-9)
            else:
                inside = (a > lo + 1e-9) and (a <= hi + 1e-9)
            if inside:
                xs.append(x)
                ys.append(y)
        f = _fit(lsq, xs, ys)
        if f:
            quads_m.append(f)
    if quads_m:
        k_med = sum(f['slope'] for f in quads_m) / len(quads_m)
        r_med = sum(f['r'] for f in quads_m) / len(quads_m)
    else:
        k_med, r_med = 0.0, 0.0
    dev_med_pct = sum(abs(y - x) for x, y in zip(cos2, norm_m)) / len(cos2) * 100.0

    t1 = {'angles': ang, 'cos2': cos2, 'reads': reads,
          'mean': means, 'norm': norm, 'i0': i0,
          'n_reads': len(reads)}

    result = {
        'k_mean': k_mean,
        'b_mean': b_mean,
        'r_mean': r_mean,
        'r_min': r_min,
        'dev_pct': dev_pct,
        'u_k': u_k,
        'k_dev_pct': (k_mean - 1.0) * 100.0,
        'I0_mW': i0,
        'n_points': len(ang),
        'ext_ratio': (min(means) / i0) if i0 else 0.0,
        'cos_check_max': cos_typo,
        'quads': quads,
        'global_k': glob.get('slope', 0.0),
        'global_b': glob.get('intercept', 0.0),
        'global_r': glob.get('r', 0.0),
        'global_u_k': glob.get('se_slope') or 0.0,
        'k_med': k_med,
        'r_med': r_med,
        'dev_med_pct': dev_med_pct,
        'dev_max': dev_max,
        'dev_max_angle': dev_max_angle,
    }

    return {'t1': t1, 'result': result,
            'provenance': data.get('provenance') or {'source': 'mock'}}
