# -*- coding: utf-8 -*-
r"""用已有的 data.json / calc.json 重渲杨氏模量报告（只为更新页脚等功能）。"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
W = r'C:\Users\lidey\Desktop\实验报告制作沙盒'
HERE = os.path.join(W, '07_流水线')
sys.path.insert(0, HERE)

import ir          # noqa: E402
import render_docx  # noqa: E402

ed = json.load(open(os.path.join(HERE, 'experiments', 'young.json'), encoding='utf-8'))
proj = os.path.join(HERE, 'projects', 'young-demo')
calc = json.load(open(os.path.join(proj, 'calc.json'), encoding='utf-8'))
md = os.path.join(HERE, 'content', 'young.md')

blocks = ir.build(ed, calc, md)
out = os.path.join(proj, 'out', '杨氏模量.docx')
render_docx.render(blocks, out, ed['name'], footer=ed.get('footer') or ed['name'])
print('ok blocks=%d  %s  %.1f KB' % (len(blocks), os.path.basename(out),
                                     os.path.getsize(out) / 1024))
