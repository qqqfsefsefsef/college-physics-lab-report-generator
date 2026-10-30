# -*- coding: utf-8 -*-
r"""让正文/表格里的 U_s、A_s、I_M、U_AK 真正排成下标。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
R = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\render_docx.py'
r = io.open(R, encoding='utf-8').read()

# ---- 1. 插入 write_rich ----
if 'def write_rich' not in r:
    anchor = "def new_p(doc, indent=False, center=F"
    assert r.count(anchor) == 1, 'new_p 锚点未命中'
    helper = '''SUB_RE = re.compile(r'([A-Za-z])_([A-Za-z0-9]+)')


def write_rich(p, text, size=12.0, bold=False, color=None, italic=False):
    """把「U_s」「U_AK」这类写法排成真下标（前面的字母正常，下划线后的字母做下标）。"""
    text = str(text)
    pos = 0
    for m in SUB_RE.finditer(text):
        if m.start() > pos:
            mk_run(p, text[pos:m.start()], size=size, bold=bold,
                   color=color or GRAY, italic=italic)
        mk_run(p, m.group(1), size=size, bold=bold, color=color or GRAY, italic=italic)
        mk_run(p, m.group(2), size=size, bold=bold, color=color or GRAY,
               italic=italic, sub=True)
        pos = m.end()
    if pos < len(text):
        mk_run(p, text[pos:], size=size, bold=bold, color=color or GRAY, italic=italic)


'''
    r = r.replace(anchor, helper + anchor)
    print('[OK] 加 write_rich()')

# 需要 re 模块
if '\nimport re' not in r:
    r = r.replace('import os\n', 'import os\nimport re\n', 1)
    print('[OK] 加 import re')

PATCH = [
    # 节标题
    ("mk_run(p, b['name'], bold=True)",
     "write_rich(p, b['name'], bold=True)"),
    # 节标题后的红字说明
    ("mk_run(q, b['note'], color=RED)",
     "write_rich(q, b['note'], color=RED)"),
    # 正文段
    ("""            mk_run(p, b['text'], bold=b.get('bold', False), color=b.get('color', GRAY),
                   size=b.get('size', 12.0))""",
     """            write_rich(p, b['text'], bold=b.get('bold', False),
                       color=b.get('color', GRAY), size=b.get('size', 12.0))"""),
    # note 段
    ("mk_run(p, b['text'], color=b.get('color', RED), size=b.get('size', 12.0))",
     "write_rich(p, b['text'], color=b.get('color', RED), size=b.get('size', 12.0))"),
    # 表/图注
    ("mk_run(p, b['text'], bold=b.get('bold', False), size=b.get('size', 10.5))",
     "write_rich(p, b['text'], bold=b.get('bold', False), size=b.get('size', 10.5))"),
    # 表格单元格
    ("""            segs = str(val).split('\\n')
            mk_run(p, segs[0], size=font, bold=bold)
            for seg in segs[1:]:
                p.add_run().add_break()
                mk_run(p, seg, size=font, bold=bold)""",
     """            segs = str(val).split('\\n')
            write_rich(p, segs[0], size=font, bold=bold)
            for seg in segs[1:]:
                p.add_run().add_break()
                write_rich(p, seg, size=font, bold=bold)"""),
]
for old, new in PATCH:
    n = r.count(old)
    if n != 1:
        print('[SKIP] 命中 %d 次：%r' % (n, old[:52]))
        continue
    r = r.replace(old, new)
    print('[OK] %r' % new.split('\n')[0][:56])

io.open(R, 'w', encoding='utf-8', newline='\n').write(r)
print('[DONE] render_docx.py %d 字符' % len(r))
