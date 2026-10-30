# -*- coding: utf-8 -*-
"""迈克耳孙干涉仪（实验 42）的确定性计算。

只做数学：从动镜位置读数 d1、d2 与条纹数 N 求波长 λ = 2|d2−d1|/N，
再从可见度两次趋于零时的镜移量估计钠光的相干长度，并给出不确定度。
接口与其它 calc_*.py 一致：calc(ed, data, lsq)，只用标准库。
"""

import math

# 仪器常数与 B 类误差限
U_B_DD_MM = 2e-5          # 动镜位置读数差 Δd 的误差限（mm），读数窗可估读到 10⁻⁵ mm
U_B_N = 0.5               # 条纹计数的误差限（个）：手掀计数器多计或少计一条
NOMINAL_DLAMBDA_NM = 0.597   # 钠双线 589.0 nm 与 589.6 nm 的波长间隔，用于估理论相干长度

_ANGLE_TRANS = str.maketrans({'−': '-', '–': '-', '—': '-', '　': ' '})


def _num(v):
    """纯数字容错：'−'→'-'、空串→nan。"""
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().translate(_ANGLE_TRANS)
    if not s:
        return float('nan')
    try:
        return float(s)
    except ValueError:
        return float('nan')


def _mean(xs):
    xs = [x for x in xs if not math.isnan(x)]
    return sum(xs) / len(xs) if xs else float('nan')


def _sd(xs):
    xs = [x for x in xs if not math.isnan(x)]
    if len(xs) < 2:
        return 0.0
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def _find_key(head, keys):
    """按 keys 的先后（优先级）在表头里找列号。"""
    for key in keys:
        for i, h in enumerate(head or []):
            if key in str(h):
                return i
    return None


def _cell(row, i):
    return row[i] if (i is not None and i < len(row)) else ''


def _blank(row):
    return all(str(x).strip() == '' for x in row)


def _rows_after(head_len, cells):
    out = []
    for row in cells[head_len:]:
        if not row or _blank(row):
            continue
        if str(_cell(row, 0)).strip().startswith('平均'):
            continue
        out.append(row)
    return out


def _read_t1(cells):
    """表 1：次数、N、d1、d2（Δd 与 λ 两列只读出来留档，一律重算）。"""
    if not cells:
        return [], []
    head = list(cells[0])
    ic_n = _find_key(head, ['测量次数', '次数'])
    ic_N = _find_key(head, ['N（个）', 'N(', '条纹数', 'N（', 'N'])
    ic_d1 = _find_key(head, ['d1'])
    ic_d2 = _find_key(head, ['d2'])
    ic_lam = _find_key(head, ['2Δd', 'λ='])
    ic_bar = _find_key(head, ['λ̄'])
    rows, cells_lambda, cell_bar = [], [], float('nan')
    for row in cells[1:]:
        if not row or _blank(row):
            continue
        if str(_cell(row, 0)).strip().startswith('平均'):
            cell_bar = _num(_cell(row, ic_bar))
            continue
        rows.append({'n': _num(_cell(row, ic_n)),
                     'N': _num(_cell(row, ic_N)),
                     'd1': _num(_cell(row, ic_d1)),
                     'd2': _num(_cell(row, ic_d2))})
        cells_lambda.append(_num(_cell(row, ic_lam)))
    return rows, [cells_lambda, cell_bar]


def _read_t2(cells):
    """表 2：次数、d1、d2。"""
    if not cells:
        return []
    head = list(cells[0])
    ic_n = _find_key(head, ['测量次数', '次数'])
    ic_d1 = _find_key(head, ['d1'])
    ic_d2 = _find_key(head, ['d2'])
    out = []
    for row in cells[1:]:
        if not row or _blank(row):
            continue
        if str(_cell(row, 0)).strip().startswith('平均'):
            continue
        out.append({'n': _num(_cell(row, ic_n)),
                    'd1': _num(_cell(row, ic_d1)),
                    'd2': _num(_cell(row, ic_d2))})
    return out


def calc(ed, data, lsq):
    tables = (data or {}).get('tables') or {}
    t1_cells = (tables.get('t1') or {}).get('cells') or []
    t2_cells = (tables.get('t2') or {}).get('cells') or []

    raw1, extra = _read_t1(t1_cells)
    raw2 = _read_t2(t2_cells)
    accepted = float(ed.get('accepted_nm', 632.8))

    # ---- 表 1：λ = 2Δd/N ----
    t1_rows, lam_list = [], []
    for k, r in enumerate(raw1, 1):
        dd = abs(r['d2'] - r['d1'])
        N = r['N']
        lam = 2.0 * dd / N * 1e6 if (N and not math.isnan(dd)) else float('nan')
        lam_list.append(lam)
        t1_rows.append({'n': k, 'N': N, 'd1': r['d1'], 'd2': r['d2'],
                        'dd': dd, 'lambda_nm': lam})
    lam_bar = _mean(lam_list)
    n_ok = len([x for x in lam_list if not math.isnan(x)])
    S_lam = _sd(lam_list)
    S_lam_bar = S_lam / math.sqrt(n_ok) if n_ok > 1 else 0.0

    # B 类：Δd 按误差限 2×10⁻⁵ mm，N 按 ±0.5 条；都用 λ = 2Δd/N 传递
    dd_mean = _mean([r['dd'] for r in t1_rows])
    N_mean = _mean([r['N'] for r in t1_rows])
    u_B_dd = (2.0 / N_mean * 1e6 * U_B_DD_MM) if N_mean else 0.0
    u_B_N = abs(lam_bar) * U_B_N / N_mean if N_mean else 0.0
    u_B_lam = math.hypot(u_B_dd, u_B_N)
    u_lam = math.hypot(S_lam_bar, u_B_lam)
    rel_u_lam = abs(u_lam / lam_bar) if lam_bar else float('nan')
    rel_err_pct = (lam_bar - accepted) / accepted * 100.0
    ratio_u = abs(lam_bar - accepted) / u_lam if u_lam else float('nan')

    # ---- 表 2：从可见度两次为零之间的镜移量估计相干长度 ----
    t2_rows, d_list = [], []
    for k, r in enumerate(raw2, 1):
        d = abs(r['d2'] - r['d1'])
        d_list.append(d)
        t2_rows.append({'n': k, 'd1': r['d1'], 'd2': r['d2'], 'd': d})
    d_bar = _mean(d_list)
    S_d = _sd(d_list)
    S_d_bar = S_d / math.sqrt(len(d_list)) if len(d_list) > 1 else 0.0
    u_d = math.hypot(S_d_bar, U_B_DD_MM * math.sqrt(2.0))
    lam0_na = 589.3
    Lc_theory_mm = lam0_na ** 2 / NOMINAL_DLAMBDA_NM / 1e6   # λ₀²/Δλ，nm→mm
    rel_Lc_pct = (d_bar - Lc_theory_mm) / Lc_theory_mm * 100.0

    result = {
        # KPI 三个键
        'lambda_nm': lam_bar,
        'rel_err_pct': rel_err_pct,
        'u_lambda_nm': u_lam,
        # 其余中间量
        'lambda_list': lam_list,
        'S_lambda_nm': S_lam,
        'S_lambdabar_nm': S_lam_bar,
        'u_B_lambda_nm': u_B_lam,
        'u_B_dd_nm': u_B_dd,
        'u_B_N_nm': u_B_N,
        'rel_u_lam': rel_u_lam,
        'accepted_nm': accepted,
        'ratio_u': ratio_u,
        'N': N_mean,
        'dd_mean_mm': dd_mean,
        'd_bar_mm': d_bar,
        'S_d_mm': S_d,
        'S_dbar_mm': S_d_bar,
        'u_d_mm': u_d,
        'rel_u_d': abs(u_d / d_bar) if d_bar else float('nan'),
        'Lc_theory_mm': Lc_theory_mm,
        'rel_Lc_pct': rel_Lc_pct,
        'lam0_na_nm': lam0_na,
        'dl_nm': NOMINAL_DLAMBDA_NM,
        # 原始记录里学生自己写下的 λ 列与平均值（供数据处理时对照）
        'cell_lambda_nm': extra[0],
        'cell_lambda_bar_nm': extra[1],
    }

    src = (data or {}).get('provenance') or {}
    return {
        'method': 'fringe_count',
        't1': {'rows': t1_rows, 'lambda_list': lam_list, 'lambda_bar': lam_bar,
               'S_lambda': S_lam, 'S_lambdabar': S_lam_bar,
               'u_B': u_B_lam, 'u_lambda': u_lam},
        't2': {'rows': t2_rows, 'd_list': d_list, 'd_bar': d_bar,
               'S_d': S_d, 'S_dbar': S_d_bar, 'u_d': u_d},
        'result': result,
        'provenance': {'source': src.get('source', 'mock'),
                       'accepted_nm': accepted},
    }
