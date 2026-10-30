# -*- coding: utf-8 -*-
r"""检查打印版 HTML 的页眉/页脚是否跟着 docx 走。"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
W = r'C:\Users\lidey\Desktop\实验报告制作沙盒\05_成品_报告'
for fn in sorted(os.listdir(W)):
    if not fn.endswith('.html'):
        continue
    p = os.path.join(W, fn)
    s = io.open(p, encoding='utf-8').read()
    m = re.search(r'<div class="runhead">(.*?)</div>\s*<div class="runfoot">(.*?)</div>', s, re.S)
    head, foot = (m.group(1), m.group(2)) if m else ('?', '?')
    print('%-46s head=%s | foot=%s | %.1f KB' % (fn[:46], head[:22], foot[:22],
                                                 len(s.encode()) / 1024))
