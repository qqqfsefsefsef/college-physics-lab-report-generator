# -*- coding: utf-8 -*-
"""Cut textbook figures out of the lecture screenshots and prepare the raw-data photo."""
from PIL import Image

W = r'C:\Users\lidey\Desktop\实验报告制作沙盒'

# 2.png : 光路图 图1 (page with 图1 at left-bottom, 图2 right)
im2 = Image.open(W + r'\2.png')
print('2.png', im2.size)
# 图1 光路图 约 x 190-490, y 950-1180  (page coords 1023x1447)
fig1 = im2.crop((185, 940, 500, 1185))
fig1 = fig1.resize((fig1.width * 3, fig1.height * 3), Image.LANCZOS)
fig1.save(W + r'\fig_light_path.png')
print('fig1', fig1.size)

# 4.png : 前面板照片 图4 + 结构接线 图5
im4 = Image.open(W + r'\4.png')
print('4.png', im4.size)
panel = im4.crop((150, 205, 875, 500))
panel = panel.resize((panel.width * 2, panel.height * 2), Image.LANCZOS)
panel.save(W + r'\fig_panel.png')
print('panel', panel.size)

wire = im4.crop((155, 540, 880, 880))
wire = wire.resize((wire.width * 2, wire.height * 2), Image.LANCZOS)
wire.save(W + r'\fig_wiring.png')
print('wire', wire.size)

# raw data photo -> jpeg for embedding (portrait)
ph = Image.open(W + r'\data_01.png').convert('RGB')
print('photo', ph.size)
w = 1800
ph2 = ph.resize((w, int(ph.height * w / ph.width)), Image.LANCZOS)
ph2.save(W + r'\data_photo.jpg', quality=90)
print('photo jpg', ph2.size)
