# -*- coding: utf-8 -*-
r"""补 UI 用到的几个样式类（mm / rtitle / rsub / empty）。"""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(P, encoding='utf-8').read()

need = {
    'mm': '提示条（实验对不上、生成失败）',
    'rtitle': '右栏小标题',
    'rsub': '右栏说明',
    'empty': '空态卡片',
}
missing = [k for k in need if ('.' + k + ' {') not in s and ('.' + k + '{') not in s
           and ('.' + k + ' ') not in s.split('</style>')[0]]
print('缺样式的类：', missing)

if missing:
    css = '''
.mm{margin:10px 0 14px;padding:12px 14px;border:1px solid #f0c36d;background:#fff8e6;
  border-radius:10px;font-size:13px;line-height:1.7;color:#7a5b12}
.mm b{color:#5c4408}
.rtitle{font-weight:700;font-size:14px;margin:2px 0 2px}
.rsub{color:#8a939c;font-size:12px;margin-bottom:10px;line-height:1.6}
.empty{border:1px dashed #d6dde5;border-radius:10px;padding:22px;text-align:center;
  color:#8a939c;font-size:13px;line-height:1.8;background:#fbfcfd}
'''
    s = s.replace('</style>', css + '</style>', 1)
    print('[OK] 已补 CSS')

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[DONE]', len(s))
