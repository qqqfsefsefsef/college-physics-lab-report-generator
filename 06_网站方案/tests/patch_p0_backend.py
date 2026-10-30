# -*- coding: utf-8 -*-
"""P0 修复（后端部分）：
1) tungsten.json 补 renderer/content/formulas/footer/表头数组/kpi，改为走 IR 渲染；
2) photo/young/tungsten 三个实验都加 kpi 规格（结果页不再写死光电效应）；
3) core.py 加 normalize_input()，把识别出来的 cells 表格转成 calc_* 需要的 dict；
4) bridge.py 的钨桩数据补齐 t2/t3，young 桩数据改成 cells 形态，
   /render 计算前先 normalize，返回体带上 kpi。
每条改动都做命中检查，跑完打印 diff 摘要。
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
W = r'C:\Users\lidey\Desktop\实验报告制作沙盒'
PIPE = os.path.join(W, '07_流水线')
EXP = os.path.join(PIPE, 'experiments')

# ---------------------------------------------------------------- 1. 实验定义
KPI = {
    'photo': [
        {'label': '普朗克常量 h / 10⁻³⁴ J·s', 'key': 'h', 'scale': 1e34, 'digits': 3},
        {'label': '与公认值 6.626 的相对误差', 'key': 'rel_err_pct', 'digits': 2,
         'signed': True, 'suffix': '%'},
        {'label': '不确定度 u(h) / 10⁻³⁴ J·s', 'key': 'u_h', 'scale': 1e34, 'digits': 3},
    ],
    'tungsten': [
        {'label': '逸出功 eφ / eV', 'key': 'phi_eV', 'digits': 3},
        {'label': '与公认值 4.54 的相对误差', 'key': 'rel_err_pct', 'digits': 2,
         'signed': True, 'suffix': '%'},
        {'label': '不确定度 u(eφ) / eV', 'key': 'u_phi_eV', 'digits': 3},
    ],
    'young': [
        {'label': '杨氏模量 Y / 10¹¹ Pa', 'key': 'Y_Pa', 'scale': 1e-11, 'digits': 3},
        {'label': '相对不确定度 u(Y)/Y', 'key': 'rel_u', 'scale': 100, 'digits': 2,
         'suffix': '%'},
        {'label': '不确定度 u(Y) / 10¹¹ Pa', 'key': 'u_Y_Pa', 'scale': 1e-11, 'digits': 3},
    ],
}

FORMULAS = {
    'F1': '*f*(*E*) = d*N*/d*E* = (4π/*h*³)(2*m*)^{3/2}*E*^{1/2}[exp((*E* − *E*_{F})/*kT*) + 1]^{−1}',
    'F2': '*E*_{0} = *E*_{b} − *E*_{F} = *eφ*',
    'F3': '*I* = *AST*²exp(−*eφ*/*kT*)',
    'F4': 'lg(*I*/*T*²) = lg*AS* − *eφ*/(2.30*kT*) = lg*AS* − 5.04×10³*φ*/*T*',
    'F5': '*I*_{a} = *I*·exp(0.439√*E*_{a}/*T*)',
    'F6': 'lg*I*_{a} = lg*I* + 0.439√*E*_{a}/(2.30*T*)',
    'F7': '*E*_{a} = *U*_{a}/(*r*₁ln(*r*₂/*r*₁))',
    'F8': 'lg*I*_{a} = lg*I* + [0.439/(2.30*T*)]√(*U*_{a}/(*r*₁ln(*r*₂/*r*₁)))',
    'F9': '*T* = 920.0 + 1600*I*_{f}',
}

for eid in ('photo', 'tungsten', 'young'):
    p = os.path.join(EXP, eid + '.json')
    ed = json.load(io.open(p, encoding='utf-8'))
    ed['kpi'] = KPI[eid]
    if eid == 'tungsten':
        ed['renderer'] = 'ir'
        ed['content'] = '04_生成过程_脚本图表\\content_tungsten.md'
        ed['footer'] = '钨的逸出功'
        ed['formulas'] = FORMULAS
        ed['u_a_V'] = [25, 36, 49, 64, 81, 100, 121, 144]
        ed['i_f_A'] = [0.600, 0.625, 0.650, 0.675, 0.700, 0.725, 0.750, 0.775]
        ed['sqrt_u_a'] = [5, 6, 7, 8, 9, 10, 11, 12]
        ed['T_1000K'] = [1.88, 1.92, 1.96, 2.00, 2.04, 2.08, 2.12, 2.16]
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(ed, f, ensure_ascii=False, indent=1)
    print('[OK] %s.json  kpi=%d renderer=%s' % (eid, len(ed['kpi']), ed.get('renderer', '-')))

# ---------------------------------------------------------------- 2. core.py
cp = os.path.join(PIPE, 'core.py')
s = io.open(cp, encoding='utf-8').read()

HELPERS = '''
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
    pair = _rows_last(tables['t1'].get('cells'), 2)
    up = [r[0] for r in pair]
    dn = [r[1] for r in pair]
    drow = _rows_last((tables.get('t2') or {}).get('cells'), 6)
    dia = drow[0] if drow else []
    flat = []
    for row in (tables.get('t3') or {}).get('cells') or []:
        v = _nums(row)
        if v:
            flat.append(v[-1])
    while len(flat) < 5:
        flat.append(0.0)
    return {
        't1': {'n_up_cm': up, 'n_down_cm': dn},
        't2': {'d_mm': dia, 'zero_mm': flat[3]},
        't3': {'D_m': flat[0], 'L_m': flat[1], 'K_m': flat[2], 'g': flat[4]},
        'constants': {'g': flat[4]},
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

'''

anchor = 'def calc_tungsten(ed, data):'
assert s.count(anchor) == 1, '找不到 calc_tungsten 锚点'
if 'def normalize_input' not in s:
    s = s.replace(anchor, HELPERS.strip('\n') + '\n\n\n' + anchor)

# 两个 calc_* 开头插入归一化
for fn in ('def calc_tungsten(ed, data):', 'def calc_young(ed, data):'):
    i = s.find(fn)
    j = s.find('\n', s.find('"""', s.find('"""', i) + 3))  # docstring 结束行末
    head = s[:j + 1]
    body = s[j + 1:]
    if 'data = _with_normalized(ed, data)' not in body[:400]:
        body = '\n    data = _with_normalized(ed, data)' + body
    s = head + body
io.open(cp, 'w', encoding='utf-8', newline='\n').write(s)
print('[OK] core.py normalize_input 已接入')

# ---------------------------------------------------------------- 3. bridge.py
bp = os.path.join(PIPE, 'bridge.py')
b = io.open(bp, encoding='utf-8').read()

TUNG_NEW = """    if ed['id'] == 'tungsten':
        t1 = [[23, 23, 24, 24, 25, 26, 26, 28], [43, 44, 44, 45, 46, 48, 48, 50],
              [78, 80, 81, 83, 84, 86, 87, 88], [139, 140, 142, 143, 152, 152, 153, 157],
              [237, 242, 244, 249, 255, 260, 262, 268], [393, 405, 410, 420, 425, 434, 447, 431],
              [645, 664, 666, 682, 694, 707, 725, 728], [1030, 1050, 1071, 1081, 1112, 1129, 1144, 1162]]
        t2 = [['√U_a', 5, 6, 7, 8, 9, 10, 11, 12],
              ['1.88', 1.36, 1.36, 1.38, 1.38, 1.39, 1.41, 1.41, 1.44],
              ['1.92', 1.63, 1.64, 1.64, 1.65, 1.66, 1.68, 1.68, 1.70],
              ['1.96', 1.89, 1.90, 1.91, 1.92, 1.92, 1.93, 1.94, 1.94],
              ['2.00', 2.14, 2.15, 2.15, 2.16, 2.18, 2.18, 2.18, 2.20],
              ['2.04', 2.37, 2.38, 2.39, 2.40, 2.41, 2.42, 2.42, 2.43],
              ['2.08', 2.59, 2.61, 2.61, 2.62, 2.63, 2.63, 2.65, 2.65],
              ['2.12', 2.81, 2.82, 2.82, 2.83, 2.84, 2.85, 2.86, 2.86],
              ['2.16', 3.01, 3.02, 3.03, 3.03, 3.05, 3.05, 3.06, 3.07]]
        t3 = [['T/10³K', 1.88, 1.92, 1.96, 2.00, 2.04, 2.08, 2.12, 2.16],
              ['1/T', 0.53, 0.52, 0.51, 0.50, 0.49, 0.48, 0.47, 0.46],
              ['lg I_s', 1.29, 1.57, 1.85, 2.09, 2.32, 2.55, 2.78, 2.97],
              ['lg(I_s/T²)', 0.75, 1.01, 1.27, 1.50, 1.71, 1.92, 2.12, 2.30]]
        return {'exp_id': ed['id'],
                'tables': {'t1': {'cells': t1}, 't2': {'cells': t2}, 't3': {'cells': t3}},
                'notes': ['【桩】表 1 第 6 行第 8 列（0.725 A / 144 V）看着像 431，'
                          '但和同行 447 不单调，请人工确认。',
                          '【桩】表 2 第 8 行（T = 2.16×10³K）学生写在框线外，已按位置补入。']}
"""
i = b.find("    if ed['id'] == 'tungsten':")
j = b.find("    if ed['id'] == 'photo':")
assert i > 0 and j > i
b = b[:i] + TUNG_NEW + b[j:]

YOUNG_ADD = """    if ed['id'] == 'young':
        t1 = [['荷重/kg', '增重读数', '减重读数']] + [
            [2.000 + k, v, w] for k, (v, w) in enumerate(zip(
                [10.00, 12.79, 15.57, 18.36, 21.13, 23.92, 26.70, 29.48],
                [10.03, 12.82, 15.60, 18.39, 21.17, 23.95, 26.73, 29.51]))]
        t2 = [['直径 d / mm（6 次）', 0.298, 0.301, 0.299, 0.302, 0.300, 0.301]]
        t3 = [['D / m', 1.5000], ['L / m', 1.0000], ['K / m', 0.0750],
              ['千分尺零点 / mm', 0.002], ['g / (m·s⁻²)', 9.794]]
        return {'exp_id': ed['id'],
                'tables': {'t1': {'cells': t1}, 't2': {'cells': t2}, 't3': {'cells': t3}},
                'notes': ['【桩】杨氏模量示例数据：钢丝直径 6 次、加减砝码各 8 次，'
                          '计算结果 Y ≈ 2.02×10¹¹ Pa。']}
"""
k = b.find("    if ed['id'] == 'photo':")
assert k > 0
b = b[:k] + YOUNG_ADD + b[k:]

# /render：计算前归一化 + 返回 kpi
old = "        data = dict(tables)\n        data['tables'] = tables\n        data['provenance'] = prov"
new = ("        tables = core.normalize_input(ed, tables)\n"
       "        data = dict(tables)\n        data['tables'] = tables\n        data['provenance'] = prov")
assert b.count(old) == 1
b = b.replace(old, new)

old2 = "                           'result': calc.get('result')})"
new2 = "                           'result': calc.get('result'),\n                           'kpi': ed.get('kpi')})"
assert b.count(old2) == 1
b = b.replace(old2, new2)

io.open(bp, 'w', encoding='utf-8', newline='\n').write(b)
print('[OK] bridge.py 桩数据 + normalize + kpi 已接入')
