# -*- coding: utf-8 -*-
import io
from docx import Document

buf = io.StringIO()
def p(x): buf.write(str(x) + '\n')

d = Document(r'C:\Users\lidey\Desktop\实验报告制作沙盒\热膨胀系数.docx')
for i, par in enumerate(d.paragraphs):
    if i < 26 or i > 40 and i < 85 or i > 104:
        continue
    p(f'--- P{i} style={par.style.name} align={par.alignment}')
    for j, r in enumerate(par.runs):
        col = None
        try:
            c = r.font.color
            col = str(c.rgb) if (c is not None and c.rgb is not None) else ('THEME:' + str(c.theme_color) if c is not None else None)
        except Exception as e:
            col = 'ERR'
        p(f'   r{j} font={r.font.name} sz={r.font.size.pt if r.font.size else None} b={r.bold} color={col} text={r.text!r}')

# section properties detail
s = d.sections[0]
p('sectPr: start_type=%s, w=%s h=%s' % (s.start_type, s.page_width, s.page_height))
open(r'C:\Users\lidey\Desktop\实验报告制作沙盒\colors_dump.txt', 'w', encoding='utf-8').write(buf.getvalue())
print('ok', len(buf.getvalue()))
