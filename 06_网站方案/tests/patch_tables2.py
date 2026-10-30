# -*- coding: utf-8 -*-
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
S = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\sections_photo.py'
s = io.open(S, encoding='utf-8').read()

# 1) curves 没有 ap 字段：从 label「435.8 nm / Φ=2 mm」里抠
old = "    T1 = {'t': 'table', 'rows': rows1, 'header': 2, 'font': 9.5, 'widths': W1,"
new = "    T1 = {'t': 'table', 'rows': rows1, 'header': 2, 'font': 9.5, 'widths': W1,"
assert s.count(old) == 1
s = s.replace(old, new)

old = "            rows1.append([c['ap'], 'I'] + [num(x, 1) for x in ii] + [''] * (8 - len(ii)))"
new = "            rows1.append([_ap(c['label']), 'I'] + [num(x, 1) for x in ii] + [''] * (8 - len(ii)))"
assert s.count(old) == 1, 'ap 行未命中'
s = s.replace(old, new)

# 2) 加 _ap 辅助函数（放在 tables 之前）
old = "def tables(calc):\n    \"\"\"三张表按"
new = '''def _ap(label):
    """从「435.8 nm / Φ=2 mm」里取出孔径写法「2 mm」。"""
    k = label.find('Φ=')
    if k < 0:
        return ''
    return label[k + 2:].strip()


def tables(calc):
    """三张表按'''
assert s.count(old) == 1, 'tables 定义未命中'
s = s.replace(old, new)

# 3) 超星位改成 1x1 无边框粘贴框
old = ("    B.append({'t': 'note', 'text': '（此处粘贴学习通章节测验的得分截图）'})")
new = ("    B.append({'t': 'table', 'rows': [['']], 'widths': [8300], 'header': 0,\n"
       "              'font': 10.5, 'row_h': 3200, 'borderless': True, 'bold_col0': False})")
assert s.count(old) == 1, '超星 note 未命中'
s = s.replace(old, new)

io.open(S, 'w', encoding='utf-8', newline='\n').write(s)
print('[OK] sections_photo.py 修好 ap / 加 _ap / 超星位改粘贴框')
