# -*- coding: utf-8 -*-
from PIL import Image
src = r'C:\Users\lidey\Desktop\实验报告制作沙盒\data_01.png'
im = Image.open(src).convert('RGB')
# (name, box in original 3072x4096 coords, scale)
regions = [
    ('z_546_neg', (250, 1240, 1450, 1460), 3.0),   # 546.1 4mm 负电压段 I 值
    ('z_t2_i',    (700, 2400, 2200, 2700), 2.6),   # 表2 I 行
    ('z_t3_rows', (250, 2980, 2950, 3400), 2.4),   # 表3 三行 U0
    ('z_435_neg', (250, 1030, 1450, 1250), 3.0),   # 435.8 2mm 负电压段
]
for name, box, s in regions:
    c = im.crop(box)
    c = c.resize((int(c.width * s), int(c.height * s)), Image.LANCZOS)
    out = rf'C:\Users\lidey\Desktop\实验报告制作沙盒\{name}.jpg'
    c.save(out, quality=94)
    print(name, c.size, out)
