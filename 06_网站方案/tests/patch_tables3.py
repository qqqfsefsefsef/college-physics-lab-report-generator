# -*- coding: utf-8 -*-
r"""第三轮（修正版）：用不含缩进锚点的替换。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
S = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\sections_photo.py'
s = io.open(S, encoding='utf-8').read()

pairs = [
    ("['波长光阑', '电压电流', '测量数组']", "['波长\\n光阑', '电压\\n电流', '测量数组']"),
    ("[c['label'], 'U_AK (V)']", "[_wl(c['label']), 'U_AK (V)']"),
    ("[['波长', '光阑电流', '测量数组', '', '']", "[['波长', '光阑\\n电流', '测量数组', '', '']"),
    ("['截止电压 U_s（V）' if k == 0 else ''", "['截止电压\\nU_s（V）' if k == 0 else ''"),
    ("[num(-x, 3) for x in t3['u0_avg']]", "[num(x, 3) for x in t3['u0_avg']]"),
]
for old, new in pairs:
    n = s.count(old)
    if n != 1:
        print('[SKIP] 命中 %d 次：%r' % (n, old))
        continue
    s = s.replace(old, new)
    print('[OK] %r -> %r' % (old[:34], new[:34]))

if 'def _wl(label):' not in s:
    old = 'def tables(calc):'
    assert s.count(old) == 1
    s = s.replace(old, '''def _wl(label):
    """「435.8 nm / Φ=2 mm」→「435.8 nm」。"""
    return label.split('/')[0].strip()


def tables(calc):''')
    print('[OK] 加 _wl()')

io.open(S, 'w', encoding='utf-8', newline='\n').write(s)
print('[DONE]', len(s), 'chars')
