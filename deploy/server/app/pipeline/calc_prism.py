# -*- coding: utf-8 -*-
"""用分光计测量三棱镜的折射率（实验 21）的确定性计算。

只做数学，不碰文字：
  表 1（AB、AC 两个反射面各读数一次，重复三次）→ 顶角 A = 180° − φ；
  表 2（左、右游标各自读汞绿线与缝像）→ 最小偏向角 δ0；
  再由 n = sin[(A+δ0)/2] / sin(A/2) 求折射率，并给出不确定度。

接口与 calc_photo / calc_young 一致：calc(ed, data, lsq)，只用标准库。
data['tables'][tid]['cells'] 是二维数组，首行是表头；读数写成「度分」字符串
（如 '175°40′'），也兼容十进制度（'175.667' 或 175.667）。
"""

import math
import re

DEG = math.pi / 180.0
VERNIER_MIN = 1.0 / 60.0                     # 角游标分度值 1′，化成度
U_B_READING = VERNIER_MIN / math.sqrt(3.0)   # B 类：Δ仪 = 1′，按均匀分布

_ANGLE_RE = re.compile(r'(\d+)\s*[°度]\s*(\d+(?:\.\d+)?)?')
_NUM_RE = re.compile(r'\d+(?:\.\d+)?')


# ----------------------------------------------------------------- 读数解析
def _num(v):
    """纯数字容错：'−'→'-'、空串→nan。"""
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace('−', '-').replace('–', '-').replace('—', '')
    if not s:
        return float('nan')
    try:
        return float(s)
    except ValueError:
        return float('nan')


def _angle(v):
    """「度分」读数 → 十进制度。

    '175°40′'、'175° 40′'、'175 40'、'175.667' 都认；空串或解析不了给 nan。
    分光计的读数都是正的（0°—360°），不处理负角度。
    """
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace('−', '-')
    if not s:
        return float('nan')
    m = _ANGLE_RE.search(s)
    if m:
        deg = float(m.group(1))
        minute = float(m.group(2)) if m.group(2) else 0.0
        return deg + minute / 60.0
    nums = _NUM_RE.findall(s)
    if len(nums) >= 2:                       # 「175 40」这种丢了符号的写法
        return float(nums[0]) + float(nums[1]) / 60.0
    if len(nums) == 1:
        return float(nums[0])
    return float('nan')


def _angdiff(a, b):
    """从读数 a 转到读数 b 的转角（度），取小于 180° 的那一支。

    望远镜（或游标盘）转过 120° 与转过 240° 在几何上是同一个夹角，
    但读数差直接相减可能得到 240°，所以先对 360° 取余再折回。
    """
    if math.isnan(a) or math.isnan(b):
        return float('nan')
    d = (b - a) % 360.0
    return 360.0 - d if d > 180.0 else d


def _mean(xs):
    xs = [x for x in xs if not math.isnan(x)]
    return sum(xs) / len(xs) if xs else float('nan')


def _sd(xs):
    """样本标准差（n−1 分母）。"""
    xs = [x for x in xs if not math.isnan(x)]
    if len(xs) < 2:
        return 0.0
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def _find(head, *keys):
    """按表头文字找列号；找不到返回 None。"""
    for i, h in enumerate(head or []):
        t = str(h)
        for k in keys:
            if k and k in t:
                return i
    return None


def _blank(row):
    return all(str(x).strip() == '' for x in row)


def _cell(row, i):
    return row[i] if (i is not None and i < len(row)) else ''


# ----------------------------------------------------------------- 表格解析
def _read_t1(cells):
    """表 1：每两行一对（AB、AC 两个反射面）。"""
    if not cells:
        return []
    head = list(cells[0])
    ic_face = _find(head, '反射面', '棱镜面')
    ic_l = _find(head, '左游标')
    ic_r = _find(head, '右游标')
    if ic_l is None:
        ic_l = 2
    if ic_r is None:
        ic_r = 3
    rows = []
    for idx, row in enumerate(cells[1:]):
        if not row or _blank(row):
            continue
        face = ''
        f = _cell(row, ic_face)
        s = str(f).upper().replace(' ', '')
        if 'AB' in s:
            face = 'AB'
        elif 'AC' in s:
            face = 'AC'
        else:
            face = 'AB' if idx % 2 == 0 else 'AC'
        rows.append({'face': face,
                     'L': _angle(_cell(row, ic_l)),
                     'R': _angle(_cell(row, ic_r))})
    pairs, cur = [], None
    for r in rows:
        if r['face'] == 'AB':
            cur = r
        elif cur is not None:
            pairs.append((cur, r))
            cur = None
    return pairs


def _read_t2(cells):
    """表 2：每两行一对（左、右游标）。"""
    if not cells:
        return []
    head = list(cells[0])
    ic_pos = _find(head, '读数的位置', '位置')
    ic_n = _find(head, '测量次数', '次数')
    ic_g = _find(head, '汞绿', '绿线')
    ic_s = _find(head, '缝像', '狭缝像')
    if ic_g is None:
        ic_g = 2
    if ic_s is None:
        ic_s = 3
    rows = []
    for row in cells[1:]:
        if not row or _blank(row):
            continue
        pos = str(_cell(row, ic_pos)).strip() or '?'
        n = _num(_cell(row, ic_n)) if ic_n is not None else float('nan')
        if not math.isnan(n) and n <= 0:
            continue
        rows.append({'pos': pos, 'n': n,
                     'green': _angle(_cell(row, ic_g)),
                     'slit': _angle(_cell(row, ic_s))})
    pairs, cur = [], None
    for r in rows:
        if not cur:
            cur = r
        else:
            pairs.append((cur, r))
            cur = None
    return pairs


# ----------------------------------------------------------------- 主计算
def calc(ed, data, lsq):
    tables = (data or {}).get('tables') or {}
    t1_cells = (tables.get('t1') or {}).get('cells') or []
    t2_cells = (tables.get('t2') or {}).get('cells') or []

    t1_pairs = _read_t1(t1_cells)
    t2_pairs = _read_t2(t2_cells)

    # ---- 顶角 A：两侧游标各算转角 φ，取平均后 A = 180° − φ ----
    t1_rows, A_list = [], []
    for k, (ab, ac) in enumerate(t1_pairs, 1):
        phi_l = _angdiff(ab['L'], ac['L'])
        phi_r = _angdiff(ab['R'], ac['R'])
        phi = _mean([phi_l, phi_r])
        A = 180.0 - phi if not math.isnan(phi) else float('nan')
        t1_rows.append({'n': k,
                        'L_ab': ab['L'], 'L_ac': ac['L'],
                        'R_ab': ab['R'], 'R_ac': ac['R'],
                        'phi_L': phi_l, 'phi_R': phi_r,
                        'phi': phi, 'A': A})
        A_list.append(A)
    A_bar = _mean(A_list)
    S_A = _sd(A_list)
    S_Abar = S_A / math.sqrt(len([a for a in A_list if not math.isnan(a)])) \
        if len([a for a in A_list if not math.isnan(a)]) > 1 else 0.0
    u_A = math.hypot(S_Abar, U_B_READING)

    # ---- 最小偏向角 δ0：绿线与缝像两次读数之差 ----
    t2_rows, groups = [], []
    for k, (a, b) in enumerate(t2_pairs, 1):
        d_a = abs(_angdiff(a['slit'], a['green']))
        d_b = abs(_angdiff(b['slit'], b['green']))
        d = _mean([d_a, d_b])
        groups.append({'n': k, 'd0_L': d_a, 'd0_R': d_b, 'd0': d})
        for side, dd in ((a, d_a), (b, d_b)):
            t2_rows.append({'n': k, 'pos': side['pos'],
                            'green': side['green'], 'slit': side['slit'],
                            'd0': dd, 'd0_pair': d})
    d0_list = [g['d0'] for g in groups]
    d0_bar = _mean(d0_list)
    n_ok = len(groups)
    S_d0 = _sd(d0_list)
    S_d0bar = S_d0 / math.sqrt(n_ok) if n_ok > 1 else 0.0
    u_d0 = math.hypot(S_d0bar, U_B_READING)

    # ---- 折射率与不确定度传递 ----
    accepted = float(ed.get('accepted_n', 1.5187))
    h = (A_bar + d0_bar) / 2.0
    n = math.sin(h * DEG) / math.sin(A_bar * DEG / 2.0) \
        if not (math.isnan(A_bar) or math.isnan(d0_bar)) else float('nan')
    c_A = 0.5 * (1.0 / math.tan(h * DEG) - 1.0 / math.tan(A_bar * DEG / 2.0)) * DEG
    c_d = 0.5 * (1.0 / math.tan(h * DEG)) * DEG
    rel_u_n = math.hypot(c_A * u_A, c_d * u_d0)
    u_n = abs(n) * rel_u_n
    rel_err_pct = (n - accepted) / accepted * 100.0
    ratio_u = abs(n - accepted) / u_n if u_n else float('nan')

    result = {
        'n': n,
        'A_deg': A_bar,
        'delta0_deg': d0_bar,
        'u_A_deg': u_A,
        'u_delta0_deg': u_d0,
        'S_A_deg': S_A,
        'S_Abar_deg': S_Abar,
        'S_delta0_deg': S_d0,
        'S_delta0bar_deg': S_d0bar,
        'rel_u_n': rel_u_n,
        'u_n': u_n,
        'accepted_n': accepted,
        'rel_err_pct': rel_err_pct,
        'ratio_u': ratio_u,
        'c_A': c_A,
        'c_delta': c_d,
        'n_meas': n_ok,
    }

    src = (data or {}).get('provenance') or {}
    return {
        'method': 'min_deviation',
        't1': {'rows': t1_rows, 'A_list': A_list, 'A_bar': A_bar,
               'S_A': S_A, 'S_Abar': S_Abar, 'u_A': u_A,
               'u_B': U_B_READING},
        't2': {'rows': t2_rows, 'groups': groups, 'd0_list': d0_list,
               'd0_bar': d0_bar, 'S_d0': S_d0, 'S_d0bar': S_d0bar,
               'u_d0': u_d0},
        'result': result,
        'provenance': {'source': src.get('source', 'mock'),
                       'accepted_n': accepted,
                       'accepted_spectrum': ed.get('accepted_spectrum', '')},
    }
