# -*- coding: utf-8 -*-
r"""把「直接生成版」docx 的表 1/2/3 完整网格打印出来（含合并信息），用于复刻版式。"""
import io
import sys

from docx import Document

sys.stdout.reconfigure(encoding='utf-8')
A = r'C:\Users\lidey\Desktop\实验报告制作沙盒\05_成品_报告\光电效应的研究.docx'
d = Document(A)
w = io.StringIO()
for ti, t in enumerate(d.tables[:3]):
    w.write('===== TABLE %d  %d rows x %d cols =====\n' % (ti + 1, len(t.rows), len(t.columns)))
    for ri, row in enumerate(t.rows):
        cells = []
        for c in row.cells:
            tc = c._tc
            mark = ''
            vm = tc.tcPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}vMerge') if tc.tcPr is not None else None
            gs = tc.tcPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}gridSpan') if tc.tcPr is not None else None
            if vm is not None:
                mark += 'v'
            if gs is not None:
                mark += 'g' + (gs.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val') or '')
            txt = c.text.strip().replace('\n', '/')
            cells.append(('%s{%s}' % (txt, mark)) if mark else txt)
        w.write('r%-2d %s\n' % (ri, ' | '.join(cells)))
    w.write('\n')
open(r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\tests\grid_A.txt', 'w', encoding='utf-8').write(w.getvalue())
print('ok')
