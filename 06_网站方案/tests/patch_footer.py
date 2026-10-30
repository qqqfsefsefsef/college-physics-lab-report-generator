# -*- coding: utf-8 -*-
r"""页脚跟着实验走：模板里是「长度测量」，生成的报告改成实验名。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
R = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\render_docx.py'
r = io.open(R, encoding='utf-8').read()

# 1) 新增 set_footer
if 'def set_footer' not in r:
    anchor = "def render(blocks, out, title=''):"
    assert r.count(anchor) == 1, 'render 锚点未命中'
    helper = '''def set_footer(doc, text):
    """把页脚里的模板文字（「长度测量」）换成这次实验的名字。"""
    if not text:
        return False
    hit = False
    for sec in doc.sections:
        for p in sec.footer.paragraphs:
            for run in p.runs:
                if '长度测量' in run.text:
                    run.text = run.text.replace('长度测量', text)
                    hit = True
            if not p.runs and p.text and '长度测量' in p.text:
                run = p.add_run(text)
                run.font.size = Pt(9)
                hit = True
    return hit


'''
    r = r.replace(anchor, helper + anchor)
    print('[OK] 加 set_footer()')

# 2) render 签名加 footer 参数并调用
old = "def render(blocks, out, title=''):"
new = "def render(blocks, out, title='', footer=None):"
assert r.count(old) == 1
r = r.replace(old, new)

old = """    doc = build_skeleton()
    if title:
        fill_title(doc, title)"""
new = """    doc = build_skeleton()
    if title:
        fill_title(doc, title)
    set_footer(doc, footer if footer is not None else title)"""
assert r.count(old) == 1, 'render 主体未命中'
r = r.replace(old, new)
print('[OK] render() 会调用 set_footer')

# 3) CLI 支持可选页脚名
old = """    blocks = js"""
new = """    blocks = js"""
io.open(R, 'w', encoding='utf-8', newline='\n').write(r)
print('[DONE]', len(r), '字符')
