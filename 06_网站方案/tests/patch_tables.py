# -*- coding: utf-8 -*-
r"""让流水线版的表格版式与「直接生成版」完全一致：
1) render_docx.add_table 支持 merges / borderless / row_h
2) sections_photo.tables() 按交付版重排（表1 18x10、表2 6x5、表3 6x7）
"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
R = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\render_docx.py'
S = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\sections_photo.py'

r = io.open(R, encoding='utf-8').read()

# ---------- 1. _cell_setup 支持无边框 ----------
old = '''def _cell_setup(tc, w):
    tcPr = tc._tc.get_or_add_tcPr()
    tcPr.append(_el('w:tcW', w=str(w), type='dxa'))
    borders = OxmlElement('w:tcBorders')
    for side in ('top', 'left', 'bottom', 'right'):
        borders.append(_el('w:' + side, val='single', sz=4, space=0, color='auto'))
    tcPr.append(borders)'''
new = '''def _cell_setup(tc, w, borderless=False):
    tcPr = tc._tc.get_or_add_tcPr()
    tcPr.append(_el('w:tcW', w=str(w), type='dxa'))
    borders = OxmlElement('w:tcBorders')
    for side in ('top', 'left', 'bottom', 'right'):
        if borderless:
            borders.append(_el('w:' + side, val='nil'))
        else:
            borders.append(_el('w:' + side, val='single', sz=4, space=0, color='auto'))
    tcPr.append(borders)'''
assert r.count(old) == 1, 'cell_setup 未命中'
r = r.replace(old, new)

# ---------- 2. add_table 支持 merges / borderless / row_h ----------
old = '''def add_table(doc, rows, widths, header=1, bold_col0=True, font=10.5, row_h=405):
    nrow = len(rows)'''
new = '''def add_table(doc, rows, widths, header=1, bold_col0=True, font=10.5, row_h=405,
              merges=None, borderless=False):
    nrow = len(rows)'''
assert r.count(old) == 1, 'add_table 头未命中'
r = r.replace(old, new)

old = '''            c = tr.cells[j]
            _cell_setup(c, widths[j])'''
new = '''            c = tr.cells[j]
            _cell_setup(c, widths[j], borderless=borderless)'''
assert r.count(old) == 1, '_cell_setup 调用未命中'
r = r.replace(old, new)

old = '''    for i, w in enumerate(widths):
        t.columns[i].width = Cm(w / 567.0)
    return t'''
new = '''    for i, w in enumerate(widths):
        t.columns[i].width = Cm(w / 567.0)
    if merges:
        for r0, c0, r1, c1 in merges:
            a, b = t.cell(r0, c0), t.cell(r1, c1)
            if a is b:
                continue
            m = a.merge(b)
            keep = m.paragraphs[0]
            for p in m.paragraphs[1:]:
                p._element.getparent().remove(p._element)
            keep.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in keep.runs:
                run.font.bold = True
    return t'''
assert r.count(old) == 1, 'add_table 尾未命中'
r = r.replace(old, new)

# ---------- 3. 分派传参 ----------
old = '''            add_table(doc, b['rows'], b['widths'], header=b.get('header', 1),
                      bold_col0=b.get('bold_col0', True), font=b.get('font', 10.5))'''
new = '''            add_table(doc, b['rows'], b['widths'], header=b.get('header', 1),
                      bold_col0=b.get('bold_col0', True), font=b.get('font', 10.5),
                      row_h=b.get('row_h', 405), merges=b.get('merges'),
                      borderless=b.get('borderless', False))'''
assert r.count(old) == 1, '分派未命中'
r = r.replace(old, new)
io.open(R, 'w', encoding='utf-8', newline='\n').write(r)
print('[OK] render_docx.py 已支持 merges / borderless / row_h')

# ---------- 4. sections_photo.tables() 按交付版重排 ----------
s = io.open(S, encoding='utf-8').read()
i, j = s.find('def tables(calc):'), s.find('def explain(calc, exp):')
assert i > 0 and j > i

NEW = '''def tables(calc):
    """三张表按「直接生成版」的版式复刻：表1 18x10、表2 6x5、表3 6x7。"""
    t1 = calc['t1']['curves']
    W1 = [1250, 1290] + [720] * 8
    rows1, mg1 = [], []
    labels = [(0, 8, 1), (8, 16, 9), (16, 22, 17)]
    for b, (a, z, first) in enumerate(labels):
        base = len(rows1)
        rows1.append(['波长光阑', '电压电流', '测量数组'] + [''] * 7)
        rows1.append(['', ''] + [str(first + k) for k in range(8)])
        mg1 += [(base, 0, base + 1, 0), (base, 1, base + 1, 1), (base, 2, base, 9)]
        for c in t1:
            u = c['u'][a:z]
            ii = c['i'][a:z]
            rows1.append([c['label'], 'U_AK (V)'] + [num(x, 0) for x in u] + [''] * (8 - len(u)))
            rows1.append([c['ap'], 'I'] + [num(x, 1) for x in ii] + [''] * (8 - len(ii)))
    T1 = {'t': 'table', 'rows': rows1, 'header': 2, 'font': 9.5, 'widths': W1,
          'merges': mg1, 'bold_col0': False, 'row_h': 380}

    t2 = calc['t2']['rows']
    rows2 = [['波长', '光阑电流', '测量数组', '', ''],
             ['', '', '1', '2', '3']]
    mg2 = [(0, 0, 1, 0), (0, 1, 1, 1), (0, 2, 0, 4)]
    for d in t2:
        base = len(rows2)
        rows2.append([d['label'], '光阑孔 Φ', '2 mm', '4 mm', '8 mm'])
        rows2.append(['', 'I（10⁻¹¹ A）', num(d['i2'], 1), num(d['i4'], 1), num(d['i8'], 1)])
        mg2.append((base, 0, base + 1, 0))
    T2 = {'t': 'table', 'rows': rows2, 'header': 2, 'font': 10.5,
          'widths': [1500, 2400, 1470, 1470, 1460], 'merges': mg2, 'bold_col0': False}

    t3 = calc['t3']
    lam, nu, reads = t3['lam'], t3['nu'], t3['reads']
    rows3 = [['波长 λ（nm）', ''] + [num(x, 1) for x in lam],
             ['频率 ν（10¹⁴ Hz）', ''] + [num(x, 3) for x in nu]]
    mg3 = [(0, 0, 0, 1), (1, 0, 1, 1)]
    for k in range(min(3, len(reads))):
        rows3.append(['截止电压 U_s（V）' if k == 0 else '', str(k + 1)] +
                     [num(x, 3) for x in reads[k]])
    mg3.append((2, 0, 2 + min(3, len(reads)) - 1, 0))
    rows3.append(['U_s 平均值（V）', ''] + [num(-x, 3) for x in t3['u0_avg']])
    mg3.append((len(rows3) - 1, 0, len(rows3) - 1, 1))
    T3 = {'t': 'table', 'rows': rows3, 'header': 2, 'font': 10.5,
          'widths': [1900, 600] + [1160] * len(lam), 'merges': mg3, 'bold_col0': False}
    return T1, T2, T3


'''
s = s[:i] + NEW + s[j:]

# 超星截图位改成 1x1 无边框粘贴框
old = "B.append({'t': 'para', 'text': '超星平台本实验在线练习得分截图（粘贴位）'})"
if old in s:
    s = s.replace(old, "B.append({'t': 'table', 'rows': [['']], 'widths': [8300],"
                       " 'header': 0, 'font': 10.5, 'row_h': 3200,"
                       " 'borderless': True, 'bold_col0': False})")
    print('[OK] 超星位已换成 1x1 无边框粘贴框')
else:
    k = s.find('超星')
    print('[WARN] 没找到超星段，附近内容：%r' % s[max(0, k - 200):k + 120])

io.open(S, 'w', encoding='utf-8', newline='\n').write(s)
print('[OK] sections_photo.py 表版式已重排')
