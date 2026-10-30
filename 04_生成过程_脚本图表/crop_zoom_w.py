# -*- coding: utf-8 -*-
from PIL import Image
import os

BASE = r'C:\Users\lidey\Desktop\实验报告制作沙盒\04_生成过程_脚本图表'
src = os.path.join(BASE, 'src_new.png')
outdir = os.path.join(BASE, 'crops_w')
im = Image.open(src).convert('RGB')

regions = {
    'z_t1_r67R': (2100, 1250, 2600, 1640),
    'z_t1_r67M': (1400, 1250, 2150, 1640),
    'z_t1_r67L': (600, 1250, 1450, 1640),
}
for name, box in regions.items():
    c = im.crop(box)
    s = min(1638 / max(c.width, c.height), 8.0)
    if s > 1.05:
        c = c.resize((int(c.width * s), int(c.height * s)), Image.LANCZOS)
    p = os.path.join(outdir, name + '.png')
    c.save(p)
    print(name, box, c.size)
