# -*- coding: utf-8 -*-
"""扫出各 sections_*.py 引用的图片文件名，以及 experiments/*.json 里的 figures 字段。"""
import io
import json
import os
import re

D = os.path.dirname(os.path.abspath(__file__))
pat = re.compile(r"['\"]((?:FIG|GEN)[^'\"]*\.(?:png|jpg))['\"]")
out = []
for f in sorted(os.listdir(D)):
    if f.startswith('sections_') and f.endswith('.py'):
        t = io.open(os.path.join(D, f), encoding='utf-8').read()
        hits = sorted(set(pat.findall(t)))
        out.append('%s  (%d)' % (f, len(hits)))
        for x in hits:
            out.append('    ' + x)
out.append('--- experiments ---')
for f in sorted(os.listdir(os.path.join(D, 'experiments'))):
    j = json.load(io.open(os.path.join(D, 'experiments', f), encoding='utf-8'))
    figs = j.get('figures') or []
    out.append('%s  %s  figures=%d  %s' % (f, j.get('name'), len(figs), figs))
txt = '\n'.join(out)
io.open(os.path.join(D, '_scan_figs.txt'), 'w', encoding='utf-8').write(txt)
print('written')
