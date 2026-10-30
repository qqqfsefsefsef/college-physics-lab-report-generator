# -*- coding: utf-8 -*-
"""bridge.mock_result 里 core 是方法内 import，模块级拿不到 -> 这里局部 import。"""
import io

BR = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\bridge.py'
b = io.open(BR, encoding='utf-8').read()
orig = b

old = """    m = core._mod('mock', ed['id']) if hasattr(core, '_mod') else None"""
new = """    try:
        import core as _c            # bridge 里的 core 都是局部 import，这里补一次
    except Exception:
        _c = None
    m = _c._mod('mock', ed['id']) if (_c is not None and hasattr(_c, '_mod')) else None"""
assert old in b
b = b.replace(old, new, 1)

assert b != orig
io.open(BR, 'w', encoding='utf-8', newline='\n').write(b)
print('[OK] mock_result fixed ->', len(b))
