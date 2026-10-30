# -*- coding: utf-8 -*-
"""Dump XML fragments we must imitate: body paragraph pPr, table tblPr, caption, image paragraph."""
import io
from docx import Document
from docx.oxml.ns import qn
from lxml import etree

W = r'C:\Users\lidey\Desktop\实验报告制作沙盒'
d = Document(W + r'\热膨胀系数.docx')
body = d.element.body
pars = d.paragraphs

buf = io.StringIO()
def p(s):
    buf.write(str(s) + '\n')

def dump(el, label):
    p('=' * 30 + ' ' + label)
    p(etree.tostring(el, pretty_print=True, encoding='unicode'))

for idx in (30, 31, 36, 88, 89, 90, 98):
    dump(pars[idx]._p, f'P{idx} text={pars[idx].text[:30]!r}')

# style Normal
st = d.styles['Normal']
dump(st.element, 'STYLE Normal')

# first table
tb = d.tables[0]
dump(tb._tbl.tblPr, 'TABLE0 tblPr')
dump(tb._tbl.find(qn('w:tblGrid')), 'TABLE0 grid')
# first two rows
for i, row in enumerate(tb.rows[:3]):
    dump(row._tr, f'TABLE0 row{i}')
dump(d.tables[1]._tbl, 'TABLE1 full')

# sectPr
dump(d.sections[0]._sectPr, 'SECTPR')
buf.write('body children tags: ' + ', '.join([c.tag.split('}')[1] for c in body]) + '\n')

from docx.oxml.ns import qn  # noqa
open(W + r'\xml_dump.txt', 'w', encoding='utf-8').write(buf.getvalue())
print('ok', len(buf.getvalue()))
