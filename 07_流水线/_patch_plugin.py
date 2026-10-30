# -*- coding: utf-8 -*-
"""把「加一个实验」收敛成纯新增：core 里加通用分派，bridge 里 mock 也走模块。

之后新增一个实验只需要 5 个新文件：
  experiments/<id>.json / sections_<id>.py / calc_<id>.py / mock_<id>.py / content/<id>.md
"""
import io

CORE = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\core.py'
BR = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\bridge.py'

# ---------------- core.py ----------------
s = io.open(CORE, encoding='utf-8').read()
orig = s

if 'import importlib' not in s:
    s = s.replace('import math', 'import importlib\nimport math', 1) if 'import math' in s else s
    if 'import importlib' not in s:          # 兜底：插在第一个 import 前
        s = 'import importlib\n' + s

anchor = "def review(ed, data):\n    out = []\n    _base_checks(ed, data, out)"
assert anchor in s
new_block = '''def _mod(prefix, eid):
    """按约定找插件模块：calc_<id>.py / checks_<id>.py / mock_<id>.py。"""
    try:
        return importlib.import_module('%s_%s' % (prefix, eid))
    except ImportError:
        return None


def calc_fn(ed):
    """返回 calc(ed, data) 可调用对象：先找 core 里的 calc_<id>，再找 calc_<id>.py。"""
    eid = ed['id']
    fn = globals().get('calc_' + eid)
    if fn:
        return fn
    m = _mod('calc', eid)
    if m and hasattr(m, 'calc'):
        return lambda e, d: m.calc(e, d, lsq)
    raise KeyError('没有 calc_%s（既不在 core.py，也没有 calc_%s.py）' % (eid, eid))


''' + anchor
s = s.replace(anchor, new_block, 1)

old_disp = """    if which == 'photo':
        out.extend(_checks_photo(data))
    return out"""
new_disp = """    if which == 'photo':
        out.extend(_checks_photo(data))
    m = _mod('checks', which) or _mod('checks', ed.get('id') or '')
    if m and hasattr(m, 'checks'):
        out.extend(m.checks(data, ed=ed))
    return out"""
assert old_disp in s
s = s.replace(old_disp, new_disp, 1)
assert s != orig
io.open(CORE, 'w', encoding='utf-8', newline='\n').write(s)
print('[OK] core.py patched ->', len(s))

# ---------------- bridge.py ----------------
b = io.open(BR, encoding='utf-8').read()
ob = b

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
b = b.replace(old, new, 1)

# calc 走通用分派
old2 = "    calc = getattr(core, 'calc_' + eid)"
if old2 in b:
    b = b.replace(old2, "    calc = core.calc_fn(ed)", 1)
else:
    raise AssertionError('calc 分派锚点没找到')

assert b != ob
io.open(BR, 'w', encoding='utf-8', newline='\n').write(b)
print('[OK] bridge.py patched ->', len(b))
