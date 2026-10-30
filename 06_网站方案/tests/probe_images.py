import base64
import io
import json
import os
import sys
import urllib.request

W = r'C:\Users\lidey\Desktop\实验报告制作沙盒'
SRC = os.path.join(W, '01_素材_数据与截图')

# 1) Pillow 能不能直接吃 HEIC？
try:
    from PIL import Image
    print('Pillow', Image.__version__, 'HEIF:', 'HEIF' in Image.OPEN or any('heif' in str(k).lower() for k in Image.OPEN))
    for name in ('IMG_20261026_213601.HEIC',):
        p = os.path.join(SRC, name)
        try:
            im = Image.open(p)
            print('  Pillow opened', name, im.size, im.mode)
        except Exception as e:
            print('  Pillow FAILED on', name, '->', type(e).__name__, str(e)[:120])
except Exception as e:
    print('no PIL', e)

print()
# 2) 素材体积/类型
for fn in sorted(os.listdir(SRC)):
    if os.path.isdir(os.path.join(SRC, fn)):
        continue
    p = os.path.join(SRC, fn)
    with open(p, 'rb') as fh:
        head = fh.read(12)
    print('%-52s %8.2f MB  magic=%s' % (fn[:52], os.path.getsize(p) / 1e6, head[:12].hex()))
