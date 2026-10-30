# -*- coding: utf-8 -*-
"""docx -> 打印版 HTML（A4 分页、页眉页脚、表格跨页控制）

用途：不依赖 LibreOffice / Word，用浏览器「打印 -> 另存为 PDF」得到最终 PDF。
输出：与 docx 同名 + _打印版.html，单文件自包含（图片 base64 内嵌）。
用法：python docx_to_print_html.py <a.docx> [<b.docx> ...]
"""
import sys, os, base64, io
from docx import Document
from docx.shared import Emu

W_NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
A_NS = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
R_NS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
WP_NS = '{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}'

HEADER_TEXT = '南京信息工程大学-大学物理实验报告'


def footer_text(doc, default='长度测量'):
    try:
        t = ' '.join(p.text for sec in doc.sections for p in sec.footer.paragraphs
                     if p.text.strip())
        return t.strip() or default
    except Exception:
        return default


def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def run_html(run):
    txt = run.text
    if not txt:
        return ''
    s = esc(txt).replace(' ', '&nbsp;')
    # 上下标：w:vertAlign
    va = run._r.find(W_NS + 'rPr')
    if va is not None:
        v = va.find(W_NS + 'vertAlign')
        if v is not None:
            val = v.get(W_NS + 'val')
            if val == 'subscript':
                s = '<sub>%s</sub>' % s
            elif val == 'superscript':
                s = '<sup>%s</sup>' % s
    if run.bold:
        s = '<b>%s</b>' % s
    if run.italic:
        s = '<i>%s</i>' % s
    return s


def para_align(p):
    try:
        j = p.paragraph_format.alignment
        return {0: 'left', 1: 'center', 2: 'right', 3: 'justify'}.get(int(j) if j is not None else 0, 'left')
    except Exception:
        return 'left'


def img_html(doc, run):
    out = []
    for dr in run._r.findall('.//' + W_NS + 'drawing'):
        blip = dr.find('.//' + A_NS + 'blip')
        if blip is None:
            continue
        rid = blip.get(R_NS + 'embed')
        try:
            part = doc.part.related_parts[rid]
        except Exception:
            continue
        blob = part.blob
        ext = os.path.splitext(part.partname)[1].lower() or '.png'
        if ext == '.jpeg':
            ext = '.jpg'
        mime = 'image/jpeg' if ext == '.jpg' else 'image/png'
        b64 = base64.b64encode(blob).decode()
        w = h = None
        ext_el = dr.find('.//' + WP_NS + 'extent')
        if ext_el is not None:
            w = int(int(ext_el.get('cx')) / 9525)
            h = int(int(ext_el.get('cy')) / 9525)
        style = ''
        if w:
            style = ' style="width:%dpx;height:%dpx"' % (w, h or 0)
        out.append('<img src="data:%s;base64,%s"%s alt="">' % (mime, b64, style))
    return ''.join(out)


def cell_inner(tc, doc):
    """单元格内容：文本段落 + 表格内的图片（如超星截图粘贴框）"""
    from docx.text.paragraph import Paragraph
    parts = []
    for p_el in tc.findall(W_NS + 'p'):
        p = Paragraph(p_el, doc)
        seg = ''
        for r in p.runs:
            seg += img_html(doc, r)
            seg += run_html(r)
        if seg:
            parts.append(seg)
    return '<br>'.join(parts)


def table_html(tbl, doc):
    # 预扫描 vMerge，用于生成 rowspan
    grid = []
    for tr in tbl._tbl.findall(W_NS + 'tr'):
        row = []
        for tc in tr.findall(W_NS + 'tc'):
            span = 1
            vm = None
            tcPr = tc.find(W_NS + 'tcPr')
            if tcPr is not None:
                gs = tcPr.find(W_NS + 'gridSpan')
                if gs is not None:
                    span = int(gs.get(W_NS + 'val') or 1)
                v = tcPr.find(W_NS + 'vMerge')
                if v is not None:
                    vm = v.get(W_NS + 'val') or 'continue'
            row.append({'tc': tc, 'span': span, 'vm': vm})
        grid.append(row)

    # 计算 rowspan
    for ri, row in enumerate(grid):
        for ci, cell in enumerate(row):
            if cell['vm'] == 'continue':
                continue
            if cell['vm'] == 'restart':
                n = 1
                for rj in range(ri + 1, len(grid)):
                    if ci < len(grid[rj]) and grid[rj][ci]['vm'] == 'continue':
                        n += 1
                        grid[rj][ci]['skip'] = True
                    else:
                        break
                cell['rowspan'] = n

    out = ['<table>']
    for row in grid:
        out.append('<tr>')
        for cell in row:
            if cell.get('skip'):
                continue
            tc = cell['tc']
            label = cell_inner(tc, doc)
            attrs = ''
            if cell['span'] > 1:
                attrs += ' colspan="%d"' % cell['span']
            if cell.get('rowspan', 1) > 1:
                attrs += ' rowspan="%d"' % cell['rowspan']
            out.append('<td%s>%s</td>' % (attrs, label))
        out.append('</tr>')
    out.append('</table>')
    return ''.join(out)


CSS = """
@page { size: A4; margin: 25.4mm 31.7mm 25.4mm 31.7mm; }
* { box-sizing: border-box; }
html, body { margin:0; padding:0; background:#f0f0f0; }
.page { width:210mm; min-height:297mm; margin:8mm auto; padding:25.4mm 31.7mm;
        background:#fff; box-shadow:0 1px 6px rgba(0,0,0,.25); position:relative; }
body { font-family: SimSun, "宋体", "Times New Roman", serif; font-size:12pt; line-height:1.5;
       color:#494949; }
p { margin:0 0 .25em 0; text-align:left; }
p.ind { text-indent:2em; }
p.center { text-align:center; }
h3 { font-size:12pt; font-weight:bold; margin:.9em 0 .35em 0; color:#494949; }
img { display:block; margin:6px auto; max-width:100%; }
table { border-collapse:collapse; width:100%; margin:6px auto; table-layout:fixed; }
td { border:1px solid #000; padding:2px 4px; font-size:10.5pt; text-align:center;
     vertical-align:middle; word-break:break-all; }
tr, img, p { break-inside: avoid; page-break-inside: avoid; }
thead { display:table-header-group; }
.runhead, .runfoot { display:none; }
@media print {
  html, body { background:#fff; }
  .page { width:auto; min-height:0; margin:0; padding:0; box-shadow:none; }
  .runhead { display:block; position:fixed; top:0; left:0; right:0; height:12mm;
             font-size:10.5pt; color:#000; border-bottom:.5pt solid #000;
             padding:0 31.7mm; text-align:center; line-height:11mm; }
  .runfoot { display:block; position:fixed; bottom:0; left:0; right:0; height:10mm;
             font-size:10.5pt; color:#000; padding:0 31.7mm; text-align:center;
             line-height:10mm; }
  body { padding-top:14mm; padding-bottom:12mm; }
  table, tr, td { page-break-inside:avoid; }
}
.toolbar { position:fixed; right:16px; top:16px; z-index:9; font:13px system-ui; }
.toolbar button { padding:8px 14px; border:1px solid #bbb; border-radius:6px; background:#fff; cursor:pointer; }
@media print { .toolbar { display:none; } }
"""


def convert(path):
    doc = Document(path)
    body = []
    body_el = doc.element.body
    for child in body_el.iterchildren():
        tag = child.tag
        if tag == W_NS + 'p':
            # 找段落对象
            from docx.text.paragraph import Paragraph
            p = Paragraph(child, doc)
            seg = ''
            for r in p.runs:
                seg += img_html(doc, r)
                seg += run_html(r)
            if not seg.strip():
                body.append('<p>&nbsp;</p>')
                continue
            cls = 'ind' if p.paragraph_format.first_line_indent else ''
            al = para_align(p)
            if al == 'center':
                cls = 'center'
            # 粗体整段的当作小标题
            if p.runs and all((r.bold for r in p.runs if r.text.strip())) and len(p.text) < 40 and al != 'center':
                body.append('<h3>%s</h3>' % seg)
            else:
                body.append('<p class="%s">%s</p>' % (cls, seg))
        elif tag == W_NS + 'tbl':
            from docx.table import Table
            t = Table(child, doc)
            body.append(table_html(t, doc))
    html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>%s</title><style>%s</style></head><body>
<div class="toolbar"><button onclick="window.print()">打印 / 另存为 PDF</button></div>
<div class="runhead">%s</div>
<div class="runfoot">%s</div>
<div class="page">
%s
</div>
</body></html>""" % (os.path.basename(path).replace('.docx', ''), CSS, HEADER_TEXT,
       footer_text(doc), '\n'.join(body))
    out = os.path.splitext(path)[0] + '_打印版.html'
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    return out, len(html), len(body)


if __name__ == '__main__':
    for p in sys.argv[1:]:
        out, size, blocks = convert(p)
        print('OK %s  %.1f KB  blocks=%d' % (out, size / 1024.0, blocks))
