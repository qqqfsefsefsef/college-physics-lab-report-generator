# -*- coding: utf-8 -*-
"""Crop src_new.png into legible blocks for manual reading."""
from PIL import Image
import os

BASE = r'C:\Users\lidey\Desktop\实验报告制作沙盒\04_生成过程_脚本图表'
src = os.path.join(BASE, 'src_new.png')
outdir = os.path.join(BASE, 'crops_w')
os.makedirs(outdir, exist_ok=True)

im = Image.open(src).convert('RGB')
print('size', im.size)

regions = {
    't1_left':   (300,  640, 1700, 1550),
    't1_right':  (1500, 640, 2600, 1550),
    't2_left':   (300, 1620, 1700, 2640),
    't2_right':  (1500, 1620, 2600, 2640),
    't3_left':   (200, 2600, 1520, 2980),
    't3_right':  (1420, 2600, 2650, 2980),
    't3_below':  (200, 2900, 2650, 3200),
}

for name, box in regions.items():
    c = im.crop(box)
    p = os.path.join(outdir, name + '.png')
    c.save(p)
    print(name, box, c.size, p)
