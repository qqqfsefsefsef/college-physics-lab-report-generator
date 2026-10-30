# -*- coding: utf-8 -*-
"""固体线膨胀系数：由 (t_i, l_i) 求 ΔL–Δt 直线斜率 K，再由 α = K/L1 求线膨胀系数。

数据流：bridge 的 mock／识别结果 → core.normalize_input（本实验没有专属归一化，
原样透传）→ 本模块 calc(ed, data, lsq) → sections_linear.build。
只用标准库；所有数字都从 cells 里解析，解析不了就用讲稿给的常量。
"""
import math

ACC_DEFAULT = 2.30e-5        # ℃⁻¹，铝（讲稿未给材料，示例数据按铝生成）
L1_DEFAULT_MM = 500.0        # 讲稿：金属棒原长 500.0 mm
U_L1_MM = 0.5                # 原长按 500.0 mm 给出，误差限按 0.5 mm
U_L_GAUGE_MM = 0.003         # 千分表示值误差限（分度值 0.001 mm）
U_T_C = 0.1                  # 温控仪分辨力／控制精度 0.1 ℃


def _num(v):
    """''、'—'、'−0.5'（U+2212）都要能转；转不了返回 None。"""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    for a, b in (('−', '-'), ('–', '-'), ('—', '-'), ('－', '-')):
        s = s.replace(a, b)
    s = s.replace(',', '').replace('％', '%')
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _row(cells, pred):
    for r in cells[1:]:
        if r and pred(str(r[0])):
            return r
    return None


def _nums(row):
    out = []
    for v in (row[1:] if row else []):
        x = _num(v)
        if x is not None:
            out.append(x)
    return out


def _mean(xs):
    return sum(xs) / float(len(xs)) if xs else 0.0


def _sxx(xs):
    m = _mean(xs)
    return sum((x - m) ** 2 for x in xs)


def calc(ed, data, lsq):
    cells = (data['tables'].get('t1') or {}).get('cells') or []
    if not cells:
        raise ValueError('表1 没有数据')
    set_row = _row(cells, lambda s: '设定' in s)
    t_row = _row(cells, lambda s: '温度' in s and '设定' not in s)
    l_row = _row(cells, lambda s: '千分表' in s)
    if t_row is None or l_row is None:
        raise ValueError('表1 里找不到「温度 t_i」或「千分表读数 l_i」行')
    set_c = _nums(set_row)
    t_c = _nums(t_row)
    l_um = _nums(l_row)
    n = min(len(t_c), len(l_um))
    t_c, l_um = t_c[:n], l_um[:n]
    if n < 3:
        raise ValueError('表1 至少要有 3 组数据（现在 %d 组）' % n)

    # 单次量：金属棒原长、千分表分度值、温控仪分辨力
    t2cells = (data['tables'].get('t2') or {}).get('cells') or []
    L1, div_mm, t_div_c = L1_DEFAULT_MM, 0.001, U_T_C
    for r in t2cells[1:]:
        lab, v = str(r[0]), (_num(r[1]) if len(r) > 1 else None)
        if v is None:
            continue
        if '原长' in lab or 'L1' in lab:
            L1 = v
        elif '分度' in lab:
            div_mm = v
        elif '分辨' in lab or '精度' in lab:
            t_div_c = v

    # 以第一次为基准：Δt = t_i − t_1，ΔL = l_i − l_1（第一次为原点）
    dt = [t - t_c[0] for t in t_c]
    dl = [l - l_um[0] for l in l_um]
    fit = lsq(dt, dl)
    K = fit['slope']                    # μm/℃
    b = fit['intercept']                # μm
    r = fit['r']
    s_resid = fit['s_resid']            # μm

    alpha = K * 1e-3 / L1               # (mm/℃)/mm = ℃⁻¹

    # ------------------------------------------------ 不确定度（A 类 + B 类）
    sxx = _sxx(dt)
    u_dl_um = math.sqrt(2.0) * U_L_GAUGE_MM * 1000.0 / math.sqrt(3.0)   # ΔL 由两次读数相减
    u_dt_c = math.sqrt(2.0) * t_div_c / math.sqrt(3.0)                  # Δt 由两次温度相减
    comp = {
        'K': abs(fit['se_slope'] / K) if K else 0.0,                    # A 类：拟合斜率的标准偏差
        'dL': u_dl_um / abs(dl[-1]) if dl[-1] else 0.0,                 # B 类：千分表示值误差
        'dt': u_dt_c / abs(dt[-1]) if dt[-1] else 0.0,                  # B 类：温度分辨力
        'L': U_L1_MM / L1,                                             # B 类：原长
    }
    rel_u = math.sqrt(sum(v * v for v in comp.values()))
    u_alpha = abs(rel_u * alpha)
    acc = float(ed.get('accepted') or ACC_DEFAULT)
    rel_err = (alpha - acc) / acc * 100.0

    # 拟合直线在最大温差处的预测值与标准偏差（正文里说明截距、残差用）
    mx = _mean(dt)
    y_pred = K * dt[-1] + b
    u_y_pred = s_resid * math.sqrt(1.0 / n + (dt[-1] - mx) ** 2 / sxx) if sxx else 0.0

    # 两点法对照（只用首尾两点，检验数据是否线性）
    alpha_end = (dl[-1] * 1e-3) / (L1 * dt[-1]) if dt[-1] else 0.0
    rel_err_end = (alpha_end - acc) / acc * 100.0

    return {
        'method': 'line_fit',
        't1': {
            'n': n,
            'set_C': set_c,
            't_C': t_c,
            'l_um': l_um,
            'dt_C': dt,
            'dL_um': dl,
        },
        't2': {
            'L1_mm': L1,
            'u_L1_mm': U_L1_MM,
            'div_mm': div_mm,
            'u_l_mm': U_L_GAUGE_MM,
            't_div_C': t_div_c,
            'u_t_C': U_T_C,
        },
        'result': {
            'alpha': alpha,
            'u_alpha': u_alpha,
            'rel_u': rel_u,
            'rel_err_pct': rel_err,
            'accepted': acc,
            'K': K,
            'b_um': b,
            'r': r,
            'r2': fit['r2'],
            's_resid_um': s_resid,
            'se_slope': fit['se_slope'],
            'y_pred_um': y_pred,
            'u_y_pred_um': u_y_pred,
            'alpha_end': alpha_end,
            'rel_err_end': rel_err_end,
            'components': comp,
            'u_dl_um': u_dl_um,
            'u_dt_C': u_dt_c,
            'dt_max': dt[-1],
            'dL_max': dl[-1],
            'n_sigma': (abs(rel_err) / 100.0 / rel_u) if rel_u else 0.0,
        },
        'provenance': data.get('provenance', {}),
    }
