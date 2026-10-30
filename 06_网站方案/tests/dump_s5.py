# -*- coding: utf-8 -*-
r"""导出核对屏 S5 的 HTML 片段与相关 JS，供改造前参考。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(P, encoding='utf-8').read()
i = s.find('id="s-review"')
j = s.find('id="s-gen"')
print('---- S5 MARKUP ----')
print(s[i - 200:i + 2000])
print('---- LEN', len(s))
for fn in ('function buildReviewFromRec', 'function acceptReview', 'function renderReport'):
    k = s.find(fn)
    if k > 0:
        print('----', fn, '----')
        print(s[k:k + 900])
