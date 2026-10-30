# -*- coding: utf-8 -*-
from PIL import Image
import os

BASE = r'C:\Users\lidey\Desktop\实验报告制作沙盒\04_生成过程_脚本图表'
FD = os.path.join(BASE, 'figures_tungsten')
out = os.path.join(BASE, 'crops_w')
os.makedirs(out, exist_ok=True)

jobs = [
    ('fig_w1.png', 'chk_w1_right', (1080, 880, 1500, 1080)),
    ('fig_w2.png', 'chk_w2_xlab', (700, 1000, 1200, 1100)),
    ('fig_w2.png', 'chk_w2_tr', (1450, 80, 1725, 200)),
    ('fig_w2.png', 'chk_w2_bot', (140, 830, 1100, 1000)),
    ('fig_w3.png', 'chk_w3_tr', (1250, 80, 1725, 200)),
    ('fig_w3.png', 'chk_w3_box', (150, 100, 950, 420)),
]
for src, name, box in jobs:
    im = Image.open(os.path.join(FD, src)).convert('RGB')
    c = im.crop(box)
    s = min(4.0, 1638.0 / max(c.width, c.height))
    if s > 1.05:
        c = c.resize((int(c.width * s), int(c.height * s)), Image.LANCZOS)
    c.save(os.path.join(out, name + '.png'))
    print(name, box, c.size)
