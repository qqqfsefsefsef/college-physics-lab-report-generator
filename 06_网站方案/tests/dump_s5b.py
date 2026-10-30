# -*- coding: utf-8 -*-
r"""看 fillResult / addMsg / chat 相关 JS，准备改文案与失败态。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(P, encoding='utf-8').read()
for fn in ('function addMsg', 'function fillResult', 'function acceptReview', 'function buildReviewFromRec'):
    i = s.find(fn)
    print('=' * 12, fn, '=' * 12)
    print(s[i:i + 1500] if i > 0 else 'NOT FOUND')
print('=' * 12, 'chat markup')
i = s.find('<div class="chat"')
print(s[i - 200:i + 200])
i = s.find('id="s-result"')
print('=' * 12, 'result markup')
print(s[i:i + 1600])
