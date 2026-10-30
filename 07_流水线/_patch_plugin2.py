# -*- coding: utf-8 -*-
"""bridge.py：mock 走 mock_<id>.py，calc 走 core.calc_fn（两处：/calc 与 /render）。"""
import io

BR = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\bridge.py'
b = io.open(BR, encoding='utf-8').read()
orig = b

# 1) mock 分派
old = 'def mock_result(ed):'
new = '''def mock_result(ed):
    """桩数据：优先用 mock_<id>.py，没有就落到下面的内置分支。"""
    m = core._mod('mock', ed['id']) if hasattr(core, '_mod') else None
    if m and hasattr(m, 'mock'):
        try:
            return m.mock(ed)
        except Exception as e:                       # 桩坏了不要拖垮页面
            return {'exp_id': ed['id'], 'tables': {},
                    'notes': ['桩数据模块出错：%s' % e]}
'''
assert old in b
assert b.count(old) == 1
b = b.replace(old, new, 1)

# 2) calc 分派（两处）
old2 = "        fn = getattr(core, 'calc_' + eid, None)\n"
new2 = ("        try:\n"
        "            fn = core.calc_fn(ed)\n"
        "        except KeyError:\n"
        "            fn = None\n")
assert b.count(old2) == 2, 'expect 2 dispatch sites, got %d' % b.count(old2)
b = b.replace(old2, new2)

assert b != orig
io.open(BR, 'w', encoding='utf-8', newline='\n').write(b)
print('[OK] bridge.py patched ->', len(b))
