"""光电效应（实验 47）的确定性计算：与已交付报告逐位一致。

表结构（识别结果 / 用户手填都用这一套）：
  t1  4 行：['435.8 nm / 2 mm', U_AK×22] / ['', I×22] / ['546.1 nm / 4 mm', U_AK×22] / ['', I×22]
  t2  3 行：['波长', 'Φ=2mm', 'Φ=4mm', 'Φ=8mm'] + 两行数据
  t3  5 行：['λ/nm', 5 个波长] / ['ν/(10¹⁴Hz)', 5 个频率] / 三次读数 3 行
"""
import math

E_C = 1.602e-19
H_ACC = 6.626e-34
C_LIGHT = 2.99792458e8
NU_LIST = [8.216, 7.410, 6.882, 5.492, 5.196]


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


def _row(rows, i):
    return [_num(v) for v in rows[i]] if i < len(rows) else []


def calc(ed, data, lsq):
    t1 = (data.get('t1') or {}).get('cells') or []
    t2 = (data.get('t2') or {}).get('cells') or []
    t3 = (data.get('t3') or {}).get('cells') or []

    # ---- 表 1：两条伏安曲线
    va = []
    for i in range(0, len(t1), 2):
        if i + 1 >= len(t1):
            break
        label = str(t1[i][0]) if t1[i] else '曲线%d' % (i // 2 + 1)
        u = [_num(v) for v in t1[i][1:]]
        cur = [_num(v) for v in t1[i + 1][1:]]
        pts = [(a, b) for a, b in zip(u, cur) if not (math.isnan(a) or math.isnan(b))]
        if pts:
            va.append({'label': label, 'u': [p[0] for p in pts], 'i': [p[1] for p in pts]})

    # ---- 表 2：饱和电流与光阑
    ip = []
    for r in t2[1:]:
        if not r or len(r) < 4:
            continue
        vals = [_num(v) for v in r[1:4]]
        if any(math.isnan(v) for v in vals):
            continue
        ip.append({'label': str(r[0]), 'i2': vals[0], 'i4': vals[1], 'i8': vals[2]})
    ip_norm = []
    for d in ip:
        if d['i2']:
            ip_norm.append({'label': d['label'],
                            'ratio': [1.0, d['i4'] / d['i2'], d['i8'] / d['i2']]})

    # ---- 表 3：截止电压三次读数
    lam = [_num(v) for v in (t3[0][1:] if len(t3) > 0 else [])]
    nu = [_num(v) for v in (t3[1][1:] if len(t3) > 1 else [])]
    reads = [_row(t3, i)[1:] for i in range(2, min(len(t3), 5))]
    n = min(len(lam), len(nu), *[len(r) for r in reads]) if reads else 0
    lam, nu, reads = lam[:n], nu[:n], [r[:n] for r in reads]
    u0_avg, u0_sd = [], []
    for k in range(n):
        col = [r[k] for r in reads if not math.isnan(r[k])]
        m = sum(col) / len(col) if col else float('nan')
        sd = (sum((x - m) ** 2 for x in col) / (len(col) - 1)) ** 0.5 if len(col) > 1 else 0.0
        u0_avg.append(round(m, 3))
        u0_sd.append(round(sd, 4))
    u_s = [abs(v) for v in u0_avg]

    # ---- 线性拟合 U_s = K·ν + b（ν 以 10^14 Hz 计）
    fit = lsq(nu, u_s) if n >= 3 else {'slope': float('nan'), 'intercept': float('nan'), 'r': 0, 'r2': 0}
    K_a14 = fit['slope']
    K_Vs = K_a14 * 1e-14
    h = E_C * K_Vs
    acc = ed.get('accepted_h') or H_ACC
    rel = (h - acc) / acc * 100.0
    u_K_Vs = fit.get('se_slope', 0.0) * 1e-14
    u_h = E_C * u_K_Vs
    nu0 = -fit['intercept'] / K_a14 if K_a14 else float('nan')
    lam0 = C_LIGHT / (nu0 * 1e14) * 1e9 if nu0 else float('nan')
    work_eV = abs(fit['intercept'])

    return {
        't1': {'curves': va},
        't2': {'rows': ip, 'norm': ip_norm},
        't3': {'lam': lam, 'nu': nu, 'reads': reads, 'u0_avg': u0_avg, 'u0_sd': u0_sd, 'u_s': u_s},
        'result': {
            'slope_a14': K_a14, 'K_Vs': K_Vs, 'h': h, 'accepted_h': acc,
            'rel_err_pct': rel, 'u_K_Vs': u_K_Vs, 'u_h': u_h,
            'intercept_V': fit['intercept'], 'r': fit.get('r'), 'r2': fit.get('r2'),
            'nu0_1e14': nu0, 'lam0_nm': lam0, 'work_eV': work_eV,
            'ratio_u': abs((h - acc) / u_h) if u_h else float('nan'),
        },
        'provenance': data.get('provenance', {}),
    }
