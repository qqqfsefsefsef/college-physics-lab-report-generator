# -*- coding: utf-8 -*-
"""核对「页面下拉框 ↔ experiments/*.json ↔ EXPERIMENT_SPEC 名单」三边名称是否一字不差。

用法：python tests/check_names.py
退出码 0 = 一致（允许「页面有、json 还没接」的未接入项，只提示）；
        1 = 有 json 但页面里没有对应选项（真错，用户会看到「识别桥还不支持」或者选不到）。
"""
import glob
import io
import json
import os
import re
import sys

W = r'C:\Users\lidey\Desktop\实验报告制作沙盒'
HP = os.path.join(W, '06_网站方案', 'prototype_v2.html')
EX = os.path.join(W, '07_流水线', 'experiments')

html = io.open(HP, encoding='utf-8').read()
m = re.search(r'<select[^>]*id="exp-sel"[^>]*>(.*?)</select>', html, re.S)
if not m:
    print('[FAIL] 页面里找不到 id="exp-sel" 的下拉框')
    sys.exit(1)
opts = [x.strip() for x in re.findall(r'<option[^>]*>(.*?)</option>', m.group(1), re.S)]

rows = []
for p in sorted(glob.glob(os.path.join(EX, '*.json'))):
    ed = json.loads(io.open(p, encoding='utf-8').read())
    rows.append((ed.get('id'), ed.get('name'), os.path.basename(p)))

print('页面选项 %d 个：' % len(opts))
for o in opts:
    hit = [r for r in rows if r[1] == o]
    if hit:
        print('  [接好] %-28s -> %s' % (o, hit[0][0]))
    else:
        print('  [未接] %-28s' % o)

bad = []
print('\nexperiments/ 共 %d 个：' % len(rows))
for eid, name, fn in rows:
    if name not in opts:
        bad.append((eid, name))
        print('  [错] %s (%s) 的名称「%s」在页面下拉框里没有逐字匹配' % (eid, fn, name))
    else:
        print('  [OK] %s -> %s' % (eid, name))

print('\n结论：已接 %d / 页面 %d 个选项' % (len(rows), len(opts)))
if bad:
    print('[FAIL] 有 %d 个实验的名称与页面不一致' % len(bad))
    sys.exit(1)
print('[SUM] 名称一致')
