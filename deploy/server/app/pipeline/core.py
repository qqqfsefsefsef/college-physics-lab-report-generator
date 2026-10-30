# -*- coding: utf-8 -*-
"""流水线核心：项目目录、闸门检查、计算。

设计约束（来自讨论）：
  ① 内容只生成一次，格式只是渲染；
  ② 数字只由代码算，模型不碰数字；
  ③ 「读图结果」必须经用户确认（闸门）才能进入计算与写作；
  ④ 项目目录可重渲染、可重算、可追溯。
"""
import json
import importlib
import math
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, 'projects')
EXP_DIR = os.path.join(HERE, 'experiments')

K_B = 1.3806505e-23
E_C = 1.602e-19
LN10 = 2.303


# ---------------------------------------------------------------- 基础 IO
def jload(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def jsave(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return path


def exp_def(exp_id):
    return jload(os.path.join(EXP_DIR, exp_id + '.json'))


def now():
    return time.strftime('%Y-%m-%d %H:%M:%S')


# ---------------------------------------------------------------- 项目
class Project:
    def __init__(self, slug):
        self.slug = slug
        self.dir = os.path.join(PROJ, slug)
        self.data_p = os.path.join(self.dir, 'data.json')
        self.calc_p = os.path.join(self.dir, 'calc.json')
        self.meta_p = os.path.join(self.dir, 'meta.json')
        self.review_p = os.path.join(self.dir, 'review.html')
        self.out = os.path.join(self.dir, 'out')
        self.figs = os.path.join(self.dir, 'figures')
        self.src = os.path.join(self.dir, 'source')

    # -- 创建
    @classmethod
    def create(cls, exp_id, slug, date=''):
        p = cls(slug)
        if os.path.exists(p.meta_p):
            raise SystemExit('项目已存在：%s' % p.dir)
        ed = exp_def(exp_id)
        if not ed:
            raise SystemExit('没有实验定义：experiments/%s.json' % exp_id)
        for d in (p.dir, p.out, p.figs, p.src):
            os.makedirs(d, exist_ok=True)
        meta = {
            'exp': exp_id,
            'exp_name': ed['name'],
            'title': ed['title'],
            'date': date,
            'created': now(),
            'formats': ['docx', 'html'],
            'gate': {'confirmed': False, 'at': None, 'by': None, 'decisions': []},
            'steps': {},
            'versions': {'pipeline': '0.1', 'calc': ed.get('calc'), 'template': '热膨胀系数.docx'},
            'model': {'read': 'stub/manual', 'write': 'stub/manual'},
        }
        jsave(p.meta_p, meta)
        jsave(p.data_p, {'exp': exp_id, 'tables': {}, 'unconfirmed': []})
        return p

    # -- 读写
    @property
    def meta(self):
        return jload(self.meta_p, {})

    def save_meta(self, m):
        jsave(self.meta_p, m)

    @property
    def data(self):
        return jload(self.data_p, {})

    def save_data(self, d):
        jsave(self.data_p, d)

    @property
    def calc(self):
        return jload(self.calc_p, {})

    def stamp(self, step, **kw):
        m = self.meta
        s = {'at': now()}
        s.update(kw)
        m.setdefault('steps', {})[step] = s
        self.save_meta(m)

    def gate_ok(self):
        return bool(self.meta.get('gate', {}).get('confirmed'))

    def require_gate(self, action):
        if not self.gate_ok():
            raise SystemExit('【闸门未通过】%s 需要在 review 之后执行 confirm：\n'
                             '  python pipeline.py confirm --slug %s --all --note "已逐格核对"\n'
                             '  或  python pipeline.py confirm --slug %s --accept <id>' % (action, self.slug, self.slug))


# ---------------------------------------------------------------- 闸门检查
def _flat(row):
    return [float(x) for x in row]


def review(ed, data):
    """返回 findings: [{id, level(block|warn|info), where, msg, current, suggest}]"""
    out = []
    t1 = data.get('tables', {}).get('t1', {})
    t2 = data.get('tables', {}).get('t2', {})
    t3 = data.get('tables', {}).get('t3', {})
    conf = data.get('confidence', {})

    ia = t1.get('i_a_uA') or []
    ua = t1.get('u_a_V') or []
    if not ia:
        out.append(dict(id='no-data', level='block', where='tables.t1', msg='还没有读入表 1 数据',
                        current=None, suggest='先 import（读图或手工录入）'))
        return out

    # 1) 行内单调性：同一 I_f 下 I_a 应随 U_a 递增
    for r, row in enumerate(ia):
        v = _flat(row)
        for c in range(1, len(v)):
            if v[c] < v[c - 1] * 0.999:
                out.append(dict(id='mono-t1-r%dc%d' % (r, c), level='warn',
                                where='表1 第 %d 行（I_f=%s）U_a=%s' % (r + 1, t1['i_f_A'][r], ua[c]),
                                msg='读数比左边一格小（%s < %s），可能是抄录或末位跳动' % (v[c], v[c - 1]),
                                current=v[c], suggest='确认是否应为 %s' % v[c - 1]))

    # 2) 量级跳变：相邻 I_f 行的 I_a 比值
    for r in range(1, len(ia)):
        a, b = _flat(ia[r - 1])[0], _flat(ia[r])[0]
        if a > 0 and not (1.05 <= b / a <= 3.2):
            out.append(dict(id='jump-r%d' % r, level='warn', where='表1 I_f %s → %s' % (t1['i_f_A'][r - 1], t1['i_f_A'][r]),
                            msg='首列电流比值 %.2f，超出常见区间（1.05~3.2）' % (b / a), current=b, suggest='核对量程是否换档'))

    # 3) 表2 与 lg(表1) 对撞
    lg2 = t2.get('lg_i_a') or []
    rows2 = t2.get('T_1000K') or []
    for r in range(min(len(lg2), len(rows2))):
        src_row = r if r < len(ia) else None
        if src_row is None:
            continue
        want = [math.log10(x) for x in _flat(ia[src_row])]
        got = _flat(lg2[r])
        for c in range(min(len(want), len(got))):
            if abs(want[c] - got[c]) > 0.01:
                out.append(dict(id='t2-r%dc%d' % (r, c), level='warn',
                                where='表2 第 %d 行（T=%s）√U_a=%s' % (r + 1, rows2[r], (t2.get('sqrt_u_a') or [])[c]),
                                msg='与 lg(表1) 差 %.3f（表1→%s，记录→%s）' % (got[c] - want[c], round(want[c], 3), got[c]),
                                current=got[c], suggest='按表1 应为 %s' % round(want[c], 3)))

    # 4) 行数/标签缺失（讲义印了 7 行，实际 8 行温度）
    if len(ia) != len(rows2):
        out.append(dict(id='rowcount', level='warn', where='表2',
                        msg='表 1 有 %d 个 I_f，表 2 只标了 %d 个温度' % (len(ia), len(rows2)),
                        current=len(rows2), suggest='多出的那一行应按 T=920.0+1600·I_f 补标签'))

    # 5) 表3 第 4 行的“单位陷阱”：lg(I_s/T²) 与 lg I_s − 2lg(T/10³) 恒差 6
    lg_i = t3.get('lg_i') or []
    lg_is_t2 = t3.get('lg_is_over_T2_written') or []
    if lg_i and lg_is_t2:
        offs = [round(float(a) - float(b), 3) for a, b in zip(lg_i, lg_is_t2)]
        out.append(dict(id='offset-6', level='info', where='表3 第 3→4 行',
                        msg='第 4 行 = 第 3 行 − 2lg(T/10³)，恒差 %.2f（=2lg1000）；只平移截距，不影响斜率与 eφ' % (sum(offs) / len(offs)),
                        current=offs[:3], suggest='保留原始写法，正文注明即可'))

    # 6) 置信度低的格子（视觉模型给的概率，手工录入时为 1）
    for cell, c in (conf or {}).items():
        if isinstance(c, (int, float)) and c < 0.9:
            out.append(dict(id='lowconf-' + cell, level='warn', where=cell,
                            msg='读图置信度 %.2f' % c, current=None, suggest='人工确认'))

    # 7) 未确认清单里还有没处理的
    for cell in data.get('unconfirmed', []):
        out.append(dict(id='unconfirmed-' + str(cell), level='block', where=str(cell),
                        msg='标记为待确认，尚未处理', current=None, suggest='给出取值或确认舍弃'))
    return out


def review_html(proj, ed, findings):
    lvl = {'block': ('必须处理', '#c0392b'), 'warn': ('建议确认', '#b8860b'), 'info': ('仅提示', '#2c7fb8')}
    rows = []
    for f in findings:
        tag, color = lvl[f['level']]
        rows.append(
            '<tr><td style="color:%s;white-space:nowrap">%s</td><td>%s</td><td>%s</td>'
            '<td>%s</td><td><code>%s</code></td><td><code>%s</code></td></tr>' % (
                color, tag, f['where'], f['msg'],
                '' if f.get('current') is None else f['current'],
                f['id'], f.get('suggest', '')))
    meta = proj.meta
    html = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>核对清单 · %s</title>
<style>
body{font-family:"Microsoft YaHei",system-ui,sans-serif;margin:28px;color:#2b3440;background:#fbfcfe}
h1{font-size:20px;margin:0 0 6px}
.sub{color:#6b7785;font-size:13px;margin-bottom:18px}
table{border-collapse:collapse;width:100%%;background:#fff;font-size:13px}
th,td{border:1px solid #dbe3ef;padding:7px 9px;text-align:left;vertical-align:top}
th{background:#f1f5fb}
.gate{padding:10px 14px;border-radius:8px;margin:16px 0;font-size:13px;
      background:%s;color:%s;border:1px solid %s}
code{background:#f3f5f9;padding:1px 4px;border-radius:3px;font-size:12px}
</style></head><body>
<h1>核对清单 · %s</h1>
<div class="sub">项目 <code>%s</code> · 实验 <code>%s</code> · 生成时间 %s · 共 %d 条</div>
<div class="gate">%s</div>
<table><thead><tr><th>级别</th><th>位置</th><th>问题</th><th>当前值</th><th>编号</th><th>建议</th></tr></thead>
<tbody>%s</tbody></table>
<div class="sub" style="margin-top:18px">确认后执行：<code>python pipeline.py confirm --slug %s --all --note "已逐格核对"</code></div>
</body></html>""" % (
        meta.get('title', ''), 
        '#eafaf0' if meta['gate']['confirmed'] else '#fff6e5',
        '#1e7b4b' if meta['gate']['confirmed'] else '#8a5a00',
        '#bfe6cf' if meta['gate']['confirmed'] else '#f0d9a8',
        meta.get('title', ''), proj.slug, meta.get('exp', ''), now(), len(findings),
        ('已确认（%s，%s）' % (meta['gate']['by'], meta['gate']['at'])) if meta['gate']['confirmed'] else '未确认——计算与导出会被拦下',
        '\n'.join(rows) or '<tr><td colspan="6">没有发现需要确认的问题</td></tr>', proj.slug)
    with open(proj.review_p, 'w', encoding='utf-8') as f:
        f.write(html)
    return proj.review_p


# ---------------------------------------------------------------- 计算
def lsq(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    k = sxy / sxx
    b = my - k * mx
    ss = sum((y - (k * x + b)) ** 2 for x, y in zip(xs, ys))
    s = math.sqrt(ss / (n - 2)) if n > 2 else 0.0
    r = sxy / math.sqrt(sxx * sum((y - my) ** 2 for y in ys))
    return dict(n=n, slope=k, intercept=b, r=r, r2=r * r, s_resid=s,
                se_slope=s / math.sqrt(sxx), se_intercept=s * math.sqrt(1.0 / n + mx * mx / sxx))


def _split_t2(t2):
    """渲染器要的是「印刷的 7 行 + 手写补的第 8 行」，这里按格式拆回去。"""
    T = list(t2['T_1000K'])
    rows = list(t2['lg_i_a'])
    out = {'sqrt_u_a': t2['sqrt_u_a'], 'T_1000K': T[:-1], 'lg_i_a': rows[:-1]}
    if len(rows) > len(T) - 1:
        out['lg_i_a_row_T216_extra'] = rows[-1]
    else:
        out['lg_i_a_row_T216_extra'] = []
    return out


# ------------------------------------------------------------------ 输入归一化
# 识别桥拿到的是「表格 cells」，calc_* 要的是带字段名的 dict。
# 每个实验一个 normalize_<id>(ed, tables)，统一由 normalize_input 分派。

def _nums(row):
    out = []
    for v in row:
        try:
            out.append(float(v))
        except Exception:
            pass
    return out


def _rows_last(cells, n):
    """每行取最后 n 个数字（行首的中文/序号标签自动丢掉）。"""
    out = []
    for row in cells or []:
        v = _nums(row)
        if len(v) >= n:
            out.append(v[-n:])
    return out


def normalize_tungsten(ed, tables):
    if not isinstance(tables.get('t1'), dict) or 'cells' not in (tables.get('t1') or {}):
        return tables
    t1 = _rows_last(tables['t1'].get('cells'), 8)
    t2 = _rows_last((tables.get('t2') or {}).get('cells'), 8)
    t3 = _rows_last((tables.get('t3') or {}).get('cells'), 8)
    T = list(ed.get('T_1000K') or [1.88, 1.92, 1.96, 2.00, 2.04, 2.08, 2.12, 2.16])
    n_f = len(ed.get('i_f_A') or []) or 8
    out = {
        't1': {'u_a_V': ed['u_a_V'], 'i_f_A': ed['i_f_A'], 'i_a_uA': t1[:n_f]},
        't2': {'sqrt_u_a': ed['sqrt_u_a'], 'T_1000K': T, 'lg_i_a': t2},
        't3': {'T_1000K': t3[0], 'inv_T_1e3_per_K': t3[1],
               'lg_i': t3[2], 'lg_is_over_T2_written': t3[3]},
    }
    return out


def normalize_young(ed, tables):
    if not isinstance(tables.get('t1'), dict) or 'cells' not in (tables.get('t1') or {}):
        return tables
    rows = _rows_last(tables['t1'].get('cells'), 3)      # 荷重 / 增重 / 减重
    m = [r[0] for r in rows]
    up = [r[1] for r in rows]
    dn = [r[2] for r in rows]

    dia, zero = [], 0.0
    for row in (tables.get('t2') or {}).get('cells') or []:
        v = _nums(row)
        label = ''.join(str(x) for x in row if not isinstance(x, (int, float)))
        if '零点' in label and v:
            zero = v[-1]
        elif len(v) >= 6:
            dia = v[-6:]

    D = L = K = None
    g = 9.794
    for row in (tables.get('t3') or {}).get('cells') or []:
        v = _nums(row)
        if not v:
            continue
        label = ''.join(str(x) for x in row if not isinstance(x, (int, float))).lower()
        val = v[-1]
        if 'g' in label and ('s' in label or 'gravity' in label):
            g = val
        elif label.startswith('d'):
            D = val
        elif label.startswith('l'):
            L = val
        elif label.startswith('k'):
            K = val
    if D is None or L is None or K is None:
        flat = []
        for row in (tables.get('t3') or {}).get('cells') or []:
            v = _nums(row)
            if v:
                flat.append(v[-1])
        while len(flat) < 3:
            flat.append(0.0)
        D = D if D is not None else flat[0]
        L = L if L is not None else flat[1]
        K = K if K is not None else flat[2]
    return {
        't1': {'m_kg': m, 'n_up_cm': up, 'n_down_cm': dn},
        't2': {'d_mm': dia, 'zero_mm': zero},
        't3': {'D_m': D, 'L_m': L, 'K_m': K},
        'constants': {'g': g},
    }


def normalize_input(ed, tables):
    fn = globals().get('normalize_' + str(ed.get('id')))
    try:
        return fn(ed, tables) if fn else tables
    except Exception:
        return tables


def _with_normalized(ed, data):
    if not isinstance(data, dict):
        return data
    t = data.get('tables') if isinstance(data.get('tables'), dict) else data
    t = normalize_input(ed, t)
    out = dict(data)
    out['tables'] = t
    for k, v in t.items():
        if isinstance(v, dict) and k.startswith('t'):
            out.setdefault(k, v)
    return out


def calc_tungsten(ed, data):
    """里查孙直线法：8 条 lg I_a–√U_a 求截距 → 主拟合 → eφ

    主拟合用【表里写下的】1/T（两位小数）与【学生写下的】lg(I_s/T²)——
    报告里写出来的数字必须与纸上记录一致，不能偷偷换成全精度重算。
    """

    data = _with_normalized(ed, data)

    t1 = data['tables']['t1']
    t2 = data['tables']['t2']
    t3 = data['tables']['t3']
    ua = t1['u_a_V']
    i_f = t1['i_f_A']
    sqrt_u = t2['sqrt_u_a']
    T = t3['T_1000K']

    rows = []
    lg_is = []
    for r, iarow in enumerate(t1['i_a_uA']):
        ys = [math.log10(x) for x in iarow]
        f = lsq(sqrt_u, ys)
        lg_is.append(f['intercept'])
        rows.append(dict(T_1000K=T[r] if r < len(T) else None, lg_of_table1=ys, **f))

    x_written = t3['inv_T_1e3_per_K']          # 表里写下的 1/T（×10⁻³K⁻¹）
    y_written = t3['lg_is_over_T2_written']    # 表里写下的 lg(I_s/T²)
    fit = lsq(x_written, y_written)
    m_true = fit['slope'] * 1e3
    phi_J = LN10 * K_B * abs(m_true)
    phi_eV = phi_J / E_C
    u_phi = LN10 * K_B * (fit['se_slope'] * 1e3) / E_C
    acc = ed.get('accepted_value_eV', 4.54)
    res = {
        'slope_plot': fit['slope'],
        'slope_true_per_K': m_true,
        'phi_J': phi_J,
        'phi_eV': phi_eV,
        'u_phi_eV': u_phi,
        'accepted_eV': acc,
        'rel_err_pct': (phi_eV - acc) / acc * 100.0,
        'ratio_u': abs(phi_eV - acc) / u_phi if u_phi else None,
    }
    # 变体：用精确 1/T（不截断）会得到另一个 eφ，仅作稳健性参考
    fit_exact = lsq([1.0 / t for t in T], y_written)
    res['phi_eV_exact_inv_T'] = LN10 * K_B * abs(fit_exact['slope'] * 1e3) / E_C

    return {
        'method': 'richardson',
        'rows': rows,
        'inv_T_1e3_written': x_written,
        'y_written': y_written,
        'fit': fit,
        'fit_exact_inv_T': fit_exact,
        'result': res,
        # ↓ 兼容既有渲染器的字段（build_report_tungsten.py 直接吃这些）
        'meta': {'constants': {'k_J_per_K': K_B, 'e_C': E_C, 'phi_accepted_eV': acc,
                               'T_calibration': 'T = 920.0 + 1600*I_f'}},
        'table1': {'u_a_V': ua, 'i_f_A': i_f, 'i_a_uA': t1['i_a_uA']},
        'table2': _split_t2(t2),
        'table3': {'T_1000K': T, 'inv_T_1e3_per_K': x_written,
                   'lg_i': t3['lg_i'], 'lg_is_over_T2_written': y_written},
        'table3_fit': fit,
        'lg_is_from_extrapolation': lg_is,
    }
# =====================================================================
# 以下：把「闸门检查」与「计算」按实验分派（覆盖上面钨专用的 review）。
# 新增实验时只需在这里加 _checks_<id> / calc_<id>，不要把检查写死。
# =====================================================================
_REVIEW_TUNGSTEN = review          # 先留一份引用，见下方 review() 重新定义


def _base_checks(ed, data, out):
    """所有实验通用的闸门项：行列数、待确认清单、低置信格子。"""
    tabs = data.get('tables', {})
    for spec in ed.get('tables', []):
        got = tabs.get(spec['id'])
        if not got:
            out.append(dict(id='missing-' + spec['id'], level='block', where=spec['id'],
                            msg='缺少 %s 的数据' % spec.get('caption', spec['id']),
                            current=None, suggest='先 import'))
            continue
        for key, val in got.items():
            if isinstance(val, list) and spec.get('shape'):
                pass  # 形状检查交给各实验自己的物理检查，避免误报
    for cell in data.get('unconfirmed', []):
        out.append(dict(id='unconfirmed-' + str(cell), level='block', where=str(cell),
                        msg='标记为待确认，尚未处理', current=None, suggest='给出取值或确认舍弃'))
    for cell, c in (data.get('confidence') or {}).items():
        if isinstance(c, (int, float)) and c < 0.9:
            out.append(dict(id='lowconf-' + cell, level='warn', where=cell,
                            msg='读图置信度 %.2f' % c, current=None, suggest='人工确认'))


def _checks_young(data):
    """杨氏模量：逐差法数据的自洽性。"""
    out = []
    t1 = data['tables']['t1']
    t2 = data['tables']['t2']
    up, dn, mean = t1['n_up_cm'], t1['n_down_cm'], t1['n_mean_cm']
    # 1) 增重/减重两次读数之差（迟滞），>0.1 cm 提示
    for i, (a, b) in enumerate(zip(up, dn)):
        if abs(b - a) > 0.10:
            out.append(dict(id='hyst-%d' % i, level='warn',
                            where='表1 第 %d 次（%.3f kg）' % (i, t1['m_kg'][i]),
                            msg='增重与减重读数差 %.3f cm，偏大（夹头滑移或砝码托摆动）' % (b - a),
                            current=b, suggest='检查该次读数，必要时重测'))
    # 2) 平均读数应随荷载单调递增
    for i in range(1, len(mean)):
        if mean[i] <= mean[i - 1]:
            out.append(dict(id='mono-%d' % i, level='block', where='表1 第 %d 次' % i,
                            msg='平均读数没有增加（%.3f → %.3f cm）' % (mean[i - 1], mean[i]),
                            current=mean[i], suggest='重读或重测'))
    # 3) 逐差法四组 N 的一致性
    Ns = t1['N_cm']
    if len(Ns) >= 2:
        nb = sum(Ns) / len(Ns)
        spread = (max(Ns) - min(Ns)) / nb
        if spread > 0.02:
            out.append(dict(id='n-spread', level='warn', where='表1 的 N₁~N₄',
                            msg='四组 N 的极差 %.2f%%（>2%%），说明线性不佳' % (spread * 100),
                            current=Ns, suggest='检查中间几次读数'))
    # 4) 直径一致性
    d = t2['d_mm']
    if max(d) - min(d) > 0.012:
        out.append(dict(id='d-spread', level='warn', where='表2 直径 6 次',
                        msg='直径极差 %.4f mm，偏大（钢丝可能不圆）' % (max(d) - min(d)),
                        current=d, suggest='换位置补测'))
    # 5) 零点读数提示
    if abs(t2.get('zero_mm', 0)) > 0.02:
        out.append(dict(id='zero', level='warn', where='表2 千分尺零点读数',
                        msg='零点读数 %.4f mm 偏大，注意修正方向' % t2['zero_mm'],
                        current=t2['zero_mm'], suggest='实际值 = 读数 − 零点'))
    return out


def _mod(prefix, eid):
    """按约定找插件模块：calc_<id>.py / checks_<id>.py / mock_<id>.py。"""
    try:
        return importlib.import_module('%s_%s' % (prefix, eid))
    except ImportError:
        return None


def calc_fn(ed):
    """返回 calc(ed, data) 可调用对象：先找 core 里的 calc_<id>，再找 calc_<id>.py。"""
    eid = ed['id']
    fn = globals().get('calc_' + eid)
    if fn:
        return fn
    m = _mod('calc', eid)
    if m and hasattr(m, 'calc'):
        return lambda e, d: m.calc(e, d, lsq)
    raise KeyError('没有 calc_%s（既不在 core.py，也没有 calc_%s.py）' % (eid, eid))


def review(ed, data):
    out = []
    _base_checks(ed, data, out)
    which = ed.get('checks') or ed.get('id')
    if which == 'tungsten':
        try:
            return _REVIEW_TUNGSTEN(ed, data)
        except KeyError:
            return out
    if which == 'young':
        out.extend(_checks_young(data))
    if which == 'photo':
        out.extend(_checks_photo(data))
    m = _mod('checks', which) or _mod('checks', ed.get('id') or '')
    if m and hasattr(m, 'checks'):
        out.extend(m.checks(data, ed=ed))
    return out


def calc_young(ed, data):
    """静态拉伸法 + 光杠杆 + 逐差法。返回渲染器与页面共用的一份 JSON。"""

    data = _with_normalized(ed, data)

    t1 = data['tables']['t1']
    t2 = data['tables']['t2']
    t3 = data['tables']['t3']
    g = (data.get('constants') or {}).get('g', 9.794)

    up = t1['n_up_cm']
    dn = t1['n_down_cm']
    mean = [round((a + b) / 2.0, 3) for a, b in zip(up, dn)]
    Ns = [round(mean[i + 4] - mean[i], 3) for i in range(4)]
    N_bar = sum(Ns) / 4.0
    S = math.sqrt(sum((x - N_bar) ** 2 for x in Ns) / 3.0)
    S_nbar = S / 2.0

    dia = t2['d_mm']
    d_bar = sum(dia) / len(dia)
    d_true = d_bar - t2.get('zero_mm', 0.0)
    S_d = math.sqrt(sum((x - d_bar) ** 2 for x in dia) / (len(dia) - 1))

    F = 4.0 * g                      # 4 kg 对应拉力
    d_m = d_true * 1e-3
    N_m = N_bar * 1e-2
    D, L, K = t3['D_m'], t3['L_m'], t3['K_m']
    Y = 8 * F * L * D / (math.pi * d_m ** 2 * K * N_m)

    u_d = math.sqrt((0.004 / 1e3) ** 2 + (S_d / math.sqrt(len(dia)) / 1e3) ** 2)
    comp = {
        'd': 2 * u_d / d_m,
        'K': t3.get('u_K_m', 0.0005) / K,
        'D': t3.get('u_D_m', 0.002) / D,
        'L': t3.get('u_L_m', 0.0005) / L,
        'F': (4 * t3.get('u_m_kg', 0.005) * g) / F,
        'N': (S_nbar * 1e-2) / N_m,
    }
    rel = math.sqrt(sum(v * v for v in comp.values()))
    u_Y = rel * Y
    acc = ed.get('accepted_value_Pa', 2.0e11)

    # 作图法对照：N（cm）–F（N）直线，斜率 dB/dF → ΔL–F 斜率 = K/(2D)*slope
    xs = [m * g for m in t1['m_kg']]
    ys = [x - mean[0] for x in mean]
    pl = lsq(xs, ys)
    slope_m = (K / (2 * D)) * pl['slope'] * 1e-2       # m/N
    Y_plot = 4 * L / (math.pi * d_m ** 2 * slope_m)

    return {
        'method': 'successive_difference',
        't1': {'m_kg': t1['m_kg'], 'n_up_cm': up, 'n_down_cm': dn, 'n_mean_cm': mean,
               'N_cm': Ns, 'N_bar_cm': N_bar, 'S_N_cm': S, 'S_Nbar_cm': S_nbar},
        't2': {'d_mm': dia, 'zero_mm': t2.get('zero_mm', 0.0), 'd_bar_mm': d_bar,
               'd_fixed_mm': d_true, 'S_d_mm': S_d},
        't3': {'D_m': D, 'u_D_m': t3.get('u_D_m', 0.002), 'L_m': L, 'u_L_m': t3.get('u_L_m', 0.0005),
               'K_m': K, 'u_K_m': t3.get('u_K_m', 0.0005), 'u_m_kg': t3.get('u_m_kg', 0.005),
               'g': g},
        'result': {
            'F_N': F, 'N_bar_m': N_m, 'Y_Pa': Y, 'u_Y_Pa': u_Y,
            'rel_u': rel, 'components': comp, 'accepted_Pa': acc,
            'rel_err_pct': (Y - acc) / acc * 100.0,
            'magnification': 2 * D / K,
            'Y_plot_Pa': Y_plot, 'plot_slope': pl,
        },
        'provenance': data.get('provenance', {}),
    }


# ---------------------------------------------------------------- 光电效应
def _f(x):
    try:
        return float(str(x).replace('−', '-').strip())
    except Exception:
        return float('nan')


def calc_photo(ed, data):
    """光电效应（实验 47）：U_s~ν 线性拟合求 h。实现在 calc_photo.py。"""
    import calc_photo as _p
    return _p.calc(ed, data, lsq)


def _checks_photo(data):
    out = []
    t3 = (data.get('t3') or {}).get('cells') or []
    if len(t3) < 5:
        out.append({'id': 'img-missing-t3', 'level': 'block', 'where': '表3',
                    'msg': '表 3 要 5 行：λ、ν、三次读数', 'current': len(t3),
                    'suggest': '重拍或手动填'})
        return out
    try:
        cols = [[_f(r[k]) for r in t3[2:5]] for k in range(1, len(t3[2]))]
        first = abs(sum(cols[0]) / 3.0)
        last = abs(sum(cols[-1]) / 3.0)
        if not first > last:
            out.append({'id': 'photo-order', 'level': 'warn', 'where': '表3',
                        'msg': '365 nm 的截止电压应该比 577 nm 大（频率越高截止电压越大）',
                        'current': [round(first, 3), round(last, 3)],
                        'suggest': '检查是否填错了行或列'})
    except Exception:
        pass
    return out

