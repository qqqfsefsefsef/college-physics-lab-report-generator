# -*- coding: utf-8 -*-
from PIL import Image
src = r'C:\Users\lidey\Desktop\实验报告制作沙盒\data_01.png'
im = Image.open(src)
print(im.size)
regions = {
    'crop_head':  (250, 200, 2900, 800),
    'crop_t1':    (250, 760, 2900, 1450),
    'crop_t1b':   (250, 1400, 2900, 2100),
    'crop_t2':    (250, 2080, 2900, 2680),
    'crop_t3':    (250, 2620, 2900, 3320),
}
for name, box in regions.items():
    c = im.crop(box)
    # upscale 1.4x for legibility of pencil handwriting
    c = c.resize((int(c.width * 1.4), int(c.height * 1.4)), Image.LANCZOS)
    out = rf'C:\Users\lidey\Desktop\实验报告制作沙盒\{name}.jpg'
    c.convert('RGB').save(out, quality=92)
    print(name, box, c.size, out)
