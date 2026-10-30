# -*- coding: utf-8 -*-
"""通用渲染器：IR（block 列表）→ docx。与实验无关，新实验不需要改这里。

IR block 形态：
  {'t':'heading', 'text':'【实验目的】10%'}
  {'t':'sect',    'name':'实验原理', 'pct':'10%', 'note':'红字说明'}   # 三段 run 的节标题
  {'t':'para',    'text':'…', 'indent':True, 'bold':False, 'color':None, 'center':False}
  {'t':'formula', 'expr':'*Y* = 8*FLD*/(π*d*^{2}*KN*)'}
  {'t':'caption', 'text':'表1 …'}                                     # 表注/图注（居中、小五）
  {'t':'table',   'rows':[[...]], 'widths':[twips...], 'header':1, 'bold_col0':True, 'font':10.5}
  {'t':'figure',  'path':'…', 'width_cm':12.6, 'caption':'图1 …'}
  {'t':'shot',    'path':'…', 'width_cm':8.2}                          # 超星截图位（1×1 无边框表）
  {'t':'note',    'text':'…', 'color':'FF0000'}
  {'t':'pagebreak'}

用法：python render_docx.py <blocks.json> <out.docx>
环境变量 PIPE_BASE 可覆盖骨架文档。
"""
import json
import os
import re
import sys

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

W = os.environ.get('DSH_WORKSPACE', r'C:\Users\lidey\Desktop\实验报告制作沙盒')
BASE = os.environ.get('PIPE_BASE', os.path.join(W, '03_参考模板_旧报告', '热膨胀系数.docx'))

GRAY = '494949'
RED = 'FF0000'
CN = '宋体'
EN = 'Times New Roman'


# ----------------------------------------------------------------- 基础
def _el(tag, **attrs):
    e = OxmlElement(tag)
    for k, v in attrs.items():
        e.set(qn('w:' + k), str(v))
    return e


def mk_run(p, text, size=12.0, bold=False, color=GRAY, italic=False,
           sub=False, sup=False, cn=CN, en=EN):
    r = p.add_run(text)
    f = r.font
    f.name = en
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.color.rgb = None
    r.font.color.rgb = _rgb(color)
    rPr = r._element.get_or_add_rPr()
    rf = rPr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts')
        rPr.insert(0, rf)
    rf.set(qn('w:ascii'), en)
    rf.set(qn('w:hAnsi'), en)
    rf.set(qn('w:cs'), en)
    rf.set(qn('w:eastAsia'), cn)
    rf.set(qn('w:hint'), 'eastAsia')
    if sub:
        rPr.append(_el('w:vertAlign', val='subscript'))
    elif sup:
        rPr.append(_el('w:vertAlign', val='superscript'))
    return r


def _rgb(hexstr):
    from docx.shared import RGBColor
    return RGBColor.from_string(hexstr or GRAY)


SUB_RE = re.compile(r'([A-Za-z])_([A-Za-z0-9]+)')


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


def new_p(doc, indent=False, center=False, left=True, space=0, keep_next=False):
    p = doc.add_paragraph()
    pPr = p._element.get_or_add_pPr()
    wc = OxmlElement('w:widowControl')
    pPr.append(wc)
    jc = 'center' if center else ('left' if left else 'both')
    pPr.append(_el('w:jc', val=jc))
    if indent:
        pPr.append(_el('w:ind', firstLineChars=200, firstLine=480))
    if space:
        pPr.append(_el('w:spacing', before=space, after=space))
    if keep_next:
        pPr.append(OxmlElement('w:keepNext'))
    return p


def parse_formula(expr):
    """迷你标记：*斜体*，_{下标}，^{上标}。返回 [(text, mode)]。"""
    parts = []
    buf = ''
    i = 0
    sub = sup = False
    while i < len(expr):
        c = expr[i]
        if c == '*' and not (i > 0 and expr[i - 1] == '\\'):
            if buf:
                parts.append((buf, 'sub' if sub else 'sup' if sup else 'i' if False else 'n'))
                buf = ''
            i += 1
            # 读取到下一个 *
            j = expr.find('*', i)
            if j < 0:
                buf += expr[i:]
                break
            seg = expr[i:j]
            parts.append((seg, 'i'))
            i = j + 1
            continue
        if c == '_' and i + 1 < len(expr) and expr[i + 1] == '{':
            if buf:
                parts.append((buf, 'n'))
                buf = ''
            j = expr.index('}', i)
            parts.append((expr[i + 2:j], 'sub'))
            i = j + 1
            continue
        if c == '^' and i + 1 < len(expr) and expr[i + 1] == '{':
            if buf:
                parts.append((buf, 'n'))
                buf = ''
            j = expr.index('}', i)
            parts.append((expr[i + 2:j], 'sup'))
            i = j + 1
            continue
        buf += c
        i += 1
    if buf:
        parts.append((buf, 'n'))
    return parts


def add_formula(doc, expr, size=12.0):
    p = new_p(doc, center=True, space=60)
    for text, mode in parse_formula(expr):
        mk_run(p, text, size=size, italic=(mode == 'i'),
               sub=(mode == 'sub'), sup=(mode == 'sup'))
    return p


# ----------------------------------------------------------------- 表格
def _cell_setup(tc, w, borderless=False):
    tcPr = tc._tc.get_or_add_tcPr()
    tcPr.append(_el('w:tcW', w=str(w), type='dxa'))
    borders = OxmlElement('w:tcBorders')
    for side in ('top', 'left', 'bottom', 'right'):
        if borderless:
            borders.append(_el('w:' + side, val='nil'))
        else:
            borders.append(_el('w:' + side, val='single', sz=4, space=0, color='auto'))
    tcPr.append(borders)
    mar = OxmlElement('w:tcMar')
    for side, v in (('top', 0), ('left', 108), ('bottom', 0), ('right', 108)):
        mar.append(_el('w:' + side, w=v, type='dxa'))
    tcPr.append(mar)
    tcPr.append(_el('w:vAlign', val='center'))


def add_table(doc, rows, widths, header=1, bold_col0=True, font=10.5, row_h=405,
              merges=None, borderless=False):
    nrow = len(rows)
    ncol = len(rows[0])
    t = doc.add_table(rows=nrow, cols=ncol)
    t.style = 'Normal Table'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblPr = t._tbl.tblPr
    tblPr.append(_el('w:tblW', w=str(sum(widths)), type='dxa'))
    for i, r in enumerate(rows):
        tr = t.rows[i]
        trPr = tr._tr.get_or_add_trPr()
        trPr.append(_el('w:trHeight', val=row_h, hRule='atLeast'))
        for j, val in enumerate(r):
            c = tr.cells[j]
            _cell_setup(c, widths[j], borderless=borderless)
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            bold = (i < header) or (bold_col0 and j == 0)
            segs = str(val).split('\n')
            write_rich(p, segs[0], size=font, bold=bold)
            for seg in segs[1:]:
                p.add_run().add_break()
                write_rich(p, seg, size=font, bold=bold)
    for i, w in enumerate(widths):
        t.columns[i].width = Cm(w / 567.0)
    if merges:
        for r0, c0, r1, c1 in merges:
            a, b = t.cell(r0, c0), t.cell(r1, c1)
            if a is b:
                continue
            m = a.merge(b)
            keep = m.paragraphs[0]
            for p in m.paragraphs[1:]:
                p._element.getparent().remove(p._element)
            keep.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in keep.runs:
                run.font.bold = True
    return t


# ----------------------------------------------------------------- 图
def add_figure(doc, path, width_cm, caption):
    p = new_p(doc, center=True, keep_next=True, space=40)
    p.add_run().add_picture(path, width=Cm(width_cm))
    cp = new_p(doc, center=True, space=40)
    mk_run(cp, caption, size=10.5)


# ----------------------------------------------------------------- 主流程
def add_shot(doc, path=None, width_cm=8.2, row_h=3200, hint=None):
    """超星截图位：1×1 无边框表。有图就竖排贴进去，没有就留一行浅灰提示。"""
    from docx.shared import Cm
    t = doc.add_table(rows=1, cols=1)
    t.autofit = False
    tbl = t._tbl
    tblPr = tbl.tblPr
    for tag in ('w:tblW', 'w:tblCellSpacing', 'w:tblLayout'):
        for e in tblPr.findall(qn(tag)):
            tblPr.remove(e)
    tblW = OxmlElement('w:tblW')
    tblW.set(qn('w:w'), '8300')
    tblW.set(qn('w:type'), 'dxa')
    tblPr.append(tblW)
    t.rules = None
    tc = t.cell(0, 0)
    _cell_setup(tc, 8300, borderless=True)
    # 行高给足，让图片竖排时不被挤
    trPr = t.rows[0]._tr.get_or_add_trPr()
    trH = OxmlElement('w:trHeight')
    trH.set(qn('w:val'), str(row_h))
    trH.set(qn('w:hRule'), 'atLeast')
    trPr.append(trH)
    tc._tc.get_or_add_tcPr()
    va = OxmlElement('w:vAlign')
    va.set(qn('w:val'), 'center')
    tc._tc.get_or_add_tcPr().append(va)
    p0 = tc.paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pPr = p0._p.get_or_add_pPr()
    for tag in ('w:ind', 'w:spacing'):
        for e in pPr.findall(qn(tag)):
            pPr.remove(e)
    ind = OxmlElement('w:ind')
    ind.set(qn('w:firstLine'), '0')
    ind.set(qn('w:firstLineChars'), '0')
    pPr.append(ind)
    if path and os.path.exists(path):
        p0.add_run().add_picture(path, width=Cm(width_cm))
    else:
        r = p0.add_run()
        r.text = hint or '（把学习通在线练习的得分截图粘贴到这里）'
        r.font.size = Pt(10.5)
        r.font.name = '宋体'
        r.font.color.rgb = _rgb('9A9A9A')
    doc.add_paragraph()
    return t


def build_skeleton():
    doc = Document(BASE)
    old = '热膨胀系数'
    for p in doc.paragraphs:
        for r in p.runs:
            if old in r.text:
                r.text = r.text.replace(old, '{{TITLE}}')
    # 截断到「学号…」行
    stop = None
    for i, p in enumerate(doc.paragraphs):
        if '学号' in p.text and '姓名' in p.text:
            stop = i
            break
    if stop is None:
        raise SystemExit('骨架里找不到学号行')
    body = doc.element.body
    keep = [c for c in body.iterchildren()][:stop + 1]
    for child in list(body.iterchildren()):
        if child.tag == qn('w:sectPr'):
            continue
        if child not in keep:
            body.remove(child)
    return doc


def fill_title(doc, title):
    for p in doc.paragraphs:
        for r in p.runs:
            if '{{TITLE}}' in r.text:
                r.text = r.text.replace('{{TITLE}}', title)
                return True
    return False


def set_footer(doc, text):
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


def render(blocks, out, title='', footer=None):
    doc = build_skeleton()
    if title:
        fill_title(doc, title)
    set_footer(doc, footer if footer is not None else title)
    for b in blocks:
        t = b['t']
        if t == 'sect':
            p = new_p(doc, space=60, keep_next=True)
            mk_run(p, '【')
            write_rich(p, b['name'], bold=True)
            mk_run(p, '】' + b.get('pct', ''))
            if b.get('note'):
                q = new_p(doc, space=40)
                write_rich(q, b['note'], color=RED)
        elif t == 'heading':
            p = new_p(doc, center=bool(b.get('center')), space=80, keep_next=True)
            mk_run(p, b['text'], bold=True, size=b.get('size', 12.0))
        elif t == 'para':
            p = new_p(doc, indent=b.get('indent', True), center=b.get('center', False),
                      space=b.get('space', 40))
            write_rich(p, b['text'], bold=b.get('bold', False),
                       color=b.get('color', GRAY), size=b.get('size', 12.0))
        elif t == 'note':
            p = new_p(doc, indent=True, space=40)
            write_rich(p, b['text'], color=b.get('color', RED), size=b.get('size', 12.0))
        elif t == 'formula':
            add_formula(doc, b['expr'])
        elif t == 'caption':
            p = new_p(doc, center=True, space=40, keep_next=True)
            write_rich(p, b['text'], bold=b.get('bold', False), size=b.get('size', 10.5))
        elif t == 'table':
            add_table(doc, b['rows'], b['widths'], header=b.get('header', 1),
                      bold_col0=b.get('bold_col0', True), font=b.get('font', 10.5),
                      row_h=b.get('row_h', 405), merges=b.get('merges'),
                      borderless=b.get('borderless', False))
        elif t == 'figure':
            add_figure(doc, b['path'], b['width_cm'], b['caption'])
        elif t == 'shot':
            add_shot(doc, b.get('path'), b.get('width_cm', 8.2),
                     b.get('row_h', 3200), b.get('hint'))
        elif t == 'pagebreak':
            doc.add_page_break()
        else:
            raise SystemExit('未知 block 类型：%r' % t)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    doc.save(out)
    return out


def main():
    if len(sys.argv) < 3:
        raise SystemExit('用法：python render_docx.py <blocks.json> <out.docx>')
    blocks = json.load(open(sys.argv[1], encoding='utf-8'))
    title = ''
    if len(sys.argv) > 3:
        title = sys.argv[3]
    out = render(blocks, sys.argv[2], title)
    print('[OK] %s' % out)


if __name__ == '__main__':
    main()
