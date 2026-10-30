# -*- coding: utf-8 -*-
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
C = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\projects\photo-demo\calc.json'
c = json.load(io.open(C, encoding='utf-8'))
for k in c['t1']['curves']:
    print('curve keys:', sorted(k.keys()))
    print('  label=%r ap=%r n_u=%d n_i=%d' % (k.get('label'), k.get('ap'),
                                              len(k['u']), len(k['i'])))
print('t2 rows[0]:', c['t2']['rows'][0])
print('t3 keys:', sorted(c['t3'].keys()))
print('u0_avg:', c['t3']['u0_avg'])

s = io.open(r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\sections_photo.py',
            encoding='utf-8').read()
i = s.find('超星')
print('---- 超星段 ----')
print(s[max(0, i - 320):i + 420])
