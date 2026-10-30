# -*- coding: utf-8 -*-
"""Build 光电效应的研究.docx from 热膨胀系数.docx skeleton + content_draft.md + data.json."""
import json
import re

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

W = r'C:\Users\lidey\Desktop\实验报告制作沙盒'
GEN = W + r'\04_生成过程_脚本图表'
BASE = W + r'\03_参考模板_旧报告\热膨胀系数.docx'
OUT = W + r'\05_成品_报告\光电效应的研究.docx'
SHOT = W + r'\01_素材_数据与截图\Screenshot_2026-10-26-22-18-26-754_com.chaoxing.m.jpg'

GRAY = '494949'
RED = 'FF0000'
CN = '宋体'
EN = 'Times New Roman'

D = json.load(open(GEN + r'\data.json', encoding='utf-8'))
T1 = D['tables']['table1']
T2 = D['tables']['table2']
T3 = D['tables']['table3']
FIT = D['fit']['with_intercept']
CHK = D['table2_check']['series']

doc = Document(BASE)


# ---------------------------------------------------------------- red notes
def red_text(idx):
    par = doc.paragraphs[idx]
    out = []
    for r in par.runs:
        col = r.font.color
        if col is not None and col.rgb is not None and str(col.rgb) == RED:
            out.append(r.text)
    return ''.join(out)


NOTE_PRINCIPLE = red_text(35)
NOTE_STEPS = red_text(72)
NOTE_DATA = red_text(87)
NOTE_EXP = red_text(91)

# ---------------------------------------------------------------- truncate
pars = doc.paragraphs
assert pars[27].text.strip().startswith('实验名称'), pars[27].text
for r in pars[27].runs:
    if r.text.strip() == '热膨胀系数':
        r.text = '光电效应的研究'

keep = pars[29]._p
body = doc.element.body
seen = False
for child in list(body):
    if child is keep:
        seen = True
        continue
    if not seen:
        continue
    if child.tag == qn('w:sectPr'):
        continue
    body.remove(child)

# ---------------------------------------------------------------- primitives
ALIGN = {'left': WD_ALIGN_PARAGRAPH.LEFT, 'center': WD_ALIGN_PARAGRAPH.CENTER,
         'right': WD_ALIGN_PARAGRAPH.RIGHT, 'justify': WD_ALIGN_PARAGRAPH.JUSTIFY}


def clean(s):
    s = re.sub(r'\s+([，。、；：？！）】》”])', r'\1', s)
    s = re.sub(r'([（【“])\s+', r'\1', s)
    s = re.sub(r'\s{2,}', ' ', s)
    return s.strip()


def mk_run(p, text, size=12, bold=False, color=GRAY, italic=False,
           sup=False, sub=False):
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = RGBColor.from_string(color)
    rPr = r._r.get_or_add_rPr()
    rf = rPr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts')
        rPr.insert(0, rf)
    rf.set(qn('w:ascii'), EN)
    rf.set(qn('w:hAnsi'), EN)
    rf.set(qn('w:eastAsia'), CN)
    rf.set(qn('w:cs'), EN)
    if sup:
        r.font.superscript = True
    if sub:
        r.font.subscript = True
    return r


def new_p(align='left', indent_chars=0, space_before=0, space_after=0,
          keep_next=False):
    p = doc.add_paragraph()
    p.alignment = ALIGN[align]
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.widow_control = True
    if indent_chars:
        pf.first_line_indent = Pt(12 * indent_chars)
    if keep_next:
        pf.keep_with_next = True
    return p


def body(text, indent=True, size=12, bold=False, color=GRAY, align='left',
         keep_next=False):
    p = new_p(align=align, indent_chars=2 if indent else 0, keep_next=keep_next)
    mk_run(p, clean(text), size=size, bold=bold, color=color)
    return p


def heading(name, pct='', note=None):
    p = new_p(keep_next=True)
    mk_run(p, '【', bold=False)
    mk_run(p, name, bold=True)
    mk_run(p, '】' + pct, bold=False)
    if note:
        mk_run(p, note, color=RED)
    return p


def formula(parts):
    """parts: list of (text, style) style in i/u/sup/sub."""
    p = new_p(align='center', space_before=6, space_after=6)
    for text, style in parts:
        if style == 'i':
            mk_run(p, text, italic=True)
        elif style == 'sup':
            mk_run(p, text, sup=True)
        elif style == 'sub':
            mk_run(p, text, sub=True)
        else:
            mk_run(p, text)
    return p


def tw(n):
    return Cm(n / 1440.0 * 2.54)


def cell_setup(cell, width_tw, size=10.5, bold=False, align='center', borders=True):
    cell.width = tw(width_tw)
    if borders:
        tcPr = cell._tc.get_or_add_tcPr()
        b = OxmlElement('w:tcBorders')
        for edge in ('top', 'left', 'bottom', 'right'):
            e = OxmlElement('w:' + edge)
            e.set(qn('w:val'), 'single')
            e.set(qn('w:sz'), '4')
            e.set(qn('w:space'), '0')
            e.set(qn('w:color'), 'auto')
            b.append(e)
        tcPr.append(b)
        mar = OxmlElement('w:tcMar')
        for edge, v in (('top', 0), ('left', 30), ('bottom', 0), ('right', 30)):
            e = OxmlElement('w:' + edge)
            e.set(qn('w:w'), str(v))
            e.set(qn('w:type'), 'dxa')
            mar.append(e)
        tcPr.append(mar)


def put(cell, text, size=10.5, bold=False, align='center'):
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p = cell.paragraphs[0]
    p.alignment = ALIGN[align]
    pf = p.paragraph_format
    pf.first_line_indent = Pt(0)
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.widow_control = True
    mk_run(p, text, size=size, bold=bold)


def put_lines(cell, lines, size=10.5, bold=False, align='center'):
    """Write several stacked lines into one (possibly merged) cell."""
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    first = cell.paragraphs[0]
    for r in list(first.runs):
        r._r.getparent().remove(r._r)
    for i, line in enumerate(lines):
        p = first if i == 0 else cell.add_paragraph()
        p.alignment = ALIGN[align]
        pf = p.paragraph_format
        pf.first_line_indent = Pt(0)
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.widow_control = True
        mk_run(p, line, size=size, bold=bold)


def new_table(rows, cols, widths):
    tbl = doc.add_table(rows=rows, cols=cols)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False  # python-docx writes <w:tblLayout w:type="fixed"/>
    for i, wv in enumerate(widths):
        tbl.columns[i].width = tw(wv)
    for i, wv in enumerate(widths):
        for r in tbl.rows:
            r.cells[i].width = tw(wv)
    return tbl


def row_height(tbl, idx, val_tw, rule='atLeast'):
    tr = tbl.rows[idx]._tr
    trPr = tr.get_or_add_trPr()
    h = OxmlElement('w:trHeight')
    h.set(qn('w:val'), str(val_tw))
    h.set(qn('w:hRule'), rule)
    trPr.append(h)


def kill_vmerge_inner_lines(tbl):
    """No horizontal rule may be drawn inside a vertically merged region."""
    for tc in tbl._tbl.iter(qn('w:tc')):
        tcPr = tc.tcPr
        if tcPr is None:
            continue
        v = tcPr.find(qn('w:vMerge'))
        if v is None or v.get(qn('w:val')) not in (None, 'continue'):
            continue
        b = tcPr.find(qn('w:tcBorders'))
        if b is None:
            continue
        top = b.find(qn('w:top'))
        if top is not None:
            top.set(qn('w:val'), 'nil')
        left = b.find(qn('w:left'))
        right = b.find(qn('w:right'))
        for e in (left, right):
            if e is not None and e.get(qn('w:val')) == 'nil':
                continue


def figure(path, width_cm, caption=None):
    p = new_p(align='center', space_before=6, space_after=3, keep_next=True)
    p.add_run().add_picture(path, width=Cm(width_cm))
    if caption:
        cp = new_p(align='center', space_after=6)
        mk_run(cp, caption, size=10.5, bold=True)


def caption(text):
    p = new_p(align='center', space_before=6, space_after=3, keep_next=True)
    mk_run(p, text, size=10.5, bold=True)
    return p


# ---------------------------------------------------------------- 实验目的
heading('实验目的', '10%')
body('1、了解光的量子性，通过实验加深对光的量子性的理解，认识光电效应的基本规律。')
body('2、测量光电管的伏安特性曲线，找出不同入射光频率下的截止电位。')
body('3、验证爱因斯坦光电方程，并求出普朗克常量。')

# ---------------------------------------------------------------- 实验仪器
heading('实验仪器')
body('本实验使用 DH—GD—3 型普朗克常量实验仪一套，主要包括：带微电流放大器的测量主机，'
     '电流量程分 10⁻⁸、10⁻⁹、10⁻¹⁰、10⁻¹¹、10⁻¹²、10⁻¹³ A 六档，面板上设有电流量程选择开关、'
     '电流调零旋钮、电压调节按钮、电压与电流数显窗口以及复位键；光电管暗箱，内装对可见光谱灵敏'
     '的真空光电管，阴极 K 与阳极 A 的引线从暗箱后部引出；高压汞灯及其镇流器（灯电源），装在'
     '可调支架上；一组滤色片，波长分别为 365.0、404.7、435.8、546.1、577.0 nm；三个可更换的'
     '光阑孔，孔径 Φ 为 2 mm、4 mm、8 mm；电压可在 −4 V～+30 V 之间连续调节。此外还有遮光罩、'
     '基准平台（用于放置汞灯与光电管暗箱并对准光路）以及专用连接线。')
figure(GEN + r'\fig_panel.png', 13.10, '图 1  普朗克常量实验仪前面板示意图')
figure(GEN + r'\fig_wiring.png', 13.10, '图 2  普朗克常量实验仪结构及接线示意图')

# ---------------------------------------------------------------- 实验原理
heading('实验原理', '10%', NOTE_PRINCIPLE)

body('（一）光电效应的基本规律', indent=False, bold=True, keep_next=True)
body('在光的照射下，金属中的电子吸收光的能量后挣脱表面束缚飞出来，这种现象称为光电效应，'
     '逸出的电子称为光电子，它们定向运动形成的电流称为光电流。这一现象是赫兹在 1887 年研究'
     '火花放电时首先发现的，此后又经过勒纳等人的反复检验才逐步弄清楚。它的意义并不只是多了'
     '一个新现象：光在与物质交换能量时表现出的“一份一份”的粒子性，正是从这里第一次被揭示出来。')
body('把实验事实归纳起来，大致可以写成四条，它们构成了后面整套测量工作的出发点。')
body('第一条，饱和光电流与入射光强成正比。在入射光频率不变的条件下，光强越大，单位时间内从'
     '阴极逸出的光电子越多，光电流也越大；当电压足够高、逸出的光电子几乎全部被阳极收集时，'
     '电流不再增加而达到饱和值 I_M，这个饱和值的大小正比于入射光强。')
body('第二条，光电效应存在一个截止频率，也叫红限频率，记作 ν₀。当入射光的频率低于 ν₀ 时，'
     '无论光强多大、照射时间多长，都没有光电子产生；而频率一旦高于 ν₀，即使光很弱，也会有'
     '光电子立刻逸出。')
body('第三条，逸出光电子的最大初动能与入射光强无关，只由入射光的频率决定，并且随着频率的升高'
     '而增大。光强改变的只是光电子的数目，不改变单个电子的能量。')
body('第四条，光电效应几乎是瞬时的。光一旦照到阴极上，光电子就在极短的时间内逸出，实测这一'
     '响应时间不超过 10⁻⁹ s，中间没有明显的“能量积累”过程。')
body('这四条里，后三条与经典的电磁理论直接冲突。按波动说，光强越大电场越强，电子受迫振动总能'
     '积累到足够的能量逸出，红限就不该存在；能量既然要靠积累，响应也就不该是瞬时的。正是这些'
     '矛盾逼出了新的光量子图像。')

body('（二）爱因斯坦光子假说与光电方程', indent=False, bold=True, keep_next=True)
body('1905 年，爱因斯坦放弃了“光的能量连续分布”的看法，提出光在发射、传播和吸收的全过程中'
     '都是一份一份的，每一份称为一个光量子，后来也叫光子；频率为 ν 的光，其光子的能量为 hν，'
     '其中 h 是普朗克常量。')
body('在这个图像下，光电效应的过程被描述得非常简单：一个电子一次性地吸收一个光子的全部能量，'
     '如果这份能量足够大，电子就能克服金属表面的束缚逃出来，剩下的部分变成它离开表面时的动能。'
     '按能量守恒，有：')
formula([('h', 'i'), ('ν', 'i'), (' = ', 'u'), ('½', 'u'), ('m', 'i'), ('v', 'i'),
         ('²', 'u'), (' + ', 'u'), ('A', 'i'), ('s', 'sub')])
body('式中 A_s 是电子从金属表面逸出所需的最小能量，称为逸出功；m 是电子的质量，v 是光电子'
     '离开金属表面时初速度的大小，½mv² 则是它离开表面时具有的最大初动能。')
body('有了这个式子，前面四条实验事实立刻都能解释得通。光强增大只意味着单位时间内的光子数目'
     '增多，被打出来的电子数目随之增多，所以饱和光电流与光强成正比；而单个光子的能量 hν 并没有'
     '变，最大初动能自然与光强无关。频率降到使 hν 已经小于 A_s 时，一个光子凑不够逸出所需的'
     '能量，光强再大也没有用，这正是红限频率存在的原因。电子吸收光子是一对一的瞬时过程，中间'
     '不需要积累能量的时间，所以响应极快。至于最大初动能随频率升高而增大，式子里 hν 与 A_s '
     '一减就写在那里了。')
body('需要强调的是，逸出功 A_s 由金属材料本身决定，对同一种材料它是定值，与入射光的频率和'
     '光强都无关；但它对表面状态相当敏感，表面氧化、吸附气体或者被手指沾污，都会让 A_s 发生'
     '改变。这一点在实验里会以“曲线不够理想、数据点散开”的形式表现出来。')

body('（三）截止电位与普朗克常量的测定', indent=False, bold=True, keep_next=True)
body('先看没有外加电压的情形。阴极 K 逸出的光电子本身就带着初动能，即使 K、A 之间不加电压，'
     '也会有电子飞到阳极形成光电流。如果在 A、K 之间加上反向电压，也就是让阳极电位低于阴极，'
     '电场对光电子的运动起阻碍作用，能到达阳极的电子减少，光电流随之下降。反向电压越大，被拦下'
     '的电子越多；当它增大到某一数值时，连初动能最大的那批电子也刚好被减速到无法到达阳极，'
     '光电流恰好降为零。这个使光电流为零的反向电压就称为光电效应的截止电位（也称遏止电压），'
     '用 U_s 表示，其数值取反向电压的绝对值。')
body('按动能定理，电子克服反向电场做的功 eU_s，恰好等于它被减掉的那部分动能，于是有：')
formula([('e', 'i'), ('U', 'i'), ('s', 'sub'), (' = ', 'u'), ('½', 'u'),
         ('m', 'i'), ('v', 'i'), ('²', 'u')])
body('这里的 e 是电子电荷的绝对值，取 1.602×10⁻¹⁹ C。要注意 U_s 对应的是初动能最大的那批'
     '电子，所以测得的 U_s 描述的是最快的光电子，而不是平均值。')
body('把上面两式联立、消去 ½mv²，就得到爱因斯坦光电方程的另一种写法：')
formula([('e', 'i'), ('U', 'i'), ('s', 'sub'), (' = ', 'u'), ('h', 'i'), ('ν', 'i'),
         (' − ', 'u'), ('A', 'i'), ('s', 'sub')])
body('它把一个可以直接测量的电压量 U_s 与入射光的频率 ν 联系了起来，式中 A_s 仍是逸出功。')
body('再把两边同除以 e，并把逸出功写成 h 与红限频率 ν₀ 的乘积，就把它整理成了一条直线方程：')
formula([('U', 'i'), ('s', 'sub'), (' = ', 'u'), ('(', 'u'), ('h', 'i'), ('/', 'u'),
         ('e', 'i'), (')', 'u'), ('ν', 'i'), (' − ', 'u'), ('(', 'u'), ('h', 'i'),
         ('/', 'u'), ('e', 'i'), (')', 'u'), ('ν', 'i'), ('₀', 'sub'),
         (' = ', 'u'), ('(', 'u'), ('h', 'i'), ('/', 'u'), ('e', 'i'), (')', 'u'),
         ('(', 'u'), ('ν', 'i'), (' − ', 'u'), ('ν', 'i'), ('₀', 'sub'), (')', 'u')])
body('从这条式子可以读出两件事。一是 U_s 与 ν 之间是线性关系，直线的斜率 K 只由 h 与 e 决定，'
     '数值上就是 h 与 e 的比值，与阴极用什么材料无关，这正是可以用它来测普朗克常量的根据；'
     '二是在 U_s 轴上直线的截距为负值，其大小等于 A_s 与 e 的比值，而在 ν 轴上的截距就是红限'
     '频率 ν₀，频率降到 ν₀ 时截止电位恰好为零，再往下就完全没有光电效应了。')
body('既然斜率 K 与 h 之间只差一个已知的电子电荷，那么只要测出几条不同频率谱线的截止电位，'
     '作 U_s～ν 直线，从图上求出斜率 K，就能算出普朗克常量：')
formula([('h', 'i'), (' = ', 'u'), ('e', 'i'), ('K', 'i')])
body('本实验要用的五条汞灯谱线波长分别为 365.0、404.7、435.8、546.1、577.0 nm，换算成频率'
     '约为 8.216、7.410、6.882、5.492、5.196 ×10¹⁴ Hz。频率跨度不算大，所以直线的斜率必须'
     '尽量测准；取点太少或者点散得厉害，算出来的 h 就会明显偏离公认值 6.626×10⁻³⁴ J·s。')
body('至于 U_s 怎么定，讲义给出了拐点法、零电流法和补偿法三种。本实验采用零电流法：在伏安特性'
     '曲线上找到电流恰好为零的那一点，把对应的反向电压的绝对值直接作为 U_s。这个做法成立的前提'
     '是三股干扰电流足够小。本仪器的微电流放大器可以分辨到 10⁻¹³ A，暗电流与阳极反向电流都只有'
     '10⁻¹³ A 量级，而且它们对各条谱线的影响大致相同，相当于给每一点加上一个几乎相同的偏移，'
     '主要影响直线的截距而不改变斜率，所以对 h 的测量结果不会造成大的偏差。')

body('（四）实验光路、伏安特性与干扰电流', indent=False, bold=True, keep_next=True)
body('把上面的原理落到仪器上，光路是这样走的：高压汞灯 S 发出包含若干条特征谱线的复色光，'
     '先经过滤色片，只让某一波长的准单色光通过；再经过光阑孔，由孔径的大小决定落到光电管阴极上'
     '的光通量；最后射进光电管，打在抽成真空的阴极 K 上。阳极 A 与阴极 K 之间加上可调电压，'
     '从 K 打出的光电子在电场作用下飞向 A，形成的电流由微电流计 G 读出。滤色片换一次，入射光的'
     '频率就换一次；光阑换一档，入射光强就变一次。由于光强与光阑孔的面积成正比，也就是与孔径的'
     '平方 Φ² 成正比，2 mm、4 mm、8 mm 三档之间的光强比大约是 1∶4∶16。')
figure(GEN + r'\fig_light_path.png', 11.20, '图 3  光电效应实验光路原理图')
body('若在 K、A 之间加加速电压，电压升高时光电流逐渐增大；电压足够高时，阴极逸出的电子几乎'
     '全部被阳极收集，电流不再随电压增大，达到饱和值 I_M。若加反向电压，电流逐渐减小，直到在'
     'U_s 附近降为零。把电压 U_AK 与光电流 I 的这一整段关系画出来，就是光电管的伏安特性曲线，'
     '它正是本实验直接测量、并由之提取截止电位的原始曲线。')
body('为了能测得准，本实验用的真空光电管应当满足几个条件：阴极材料对全部可见光谱都比较灵敏；'
     '阳极做成包围阴极的形状，这样即使阳极处于负电位，大部分光电子仍然能射到阳极上；阳极表面'
     '不发生光电效应，不会产生反向电流；暗电流足够小。实际的光电管并不能完全满足这些要求，'
     '于是就有了三种干扰电流。')
body('第一种是暗电流。光电管在没有光照时也有微弱电流，它由两部分组成：阴极在常温下热电子发射'
     '形成的热电流，以及阳极与阴极之间绝缘材料不理想造成的漏电流。暗电流随外加电压近似线性变化，'
     '是一层必须扣除的背景。')
body('第二种是本底电流。周围环境的杂散光漏进光电管，打在阴极上同样会产生光电子，形成本底电流。'
     '实验中靠遮光罩和暗箱把它压到最小。')
body('第三种是反向电流。制作光电管时，阳极 A 上难免溅上阴极材料，光照射到 A 上时，A 也会逸出'
     '光电子；另外，一部分从 K 逸出的光电子会被 A 表面反射回来。当 A、K 之间加反向电压时，'
     '这个电压对从 K 出来的电子起减速作用，对从 A 发出和从 A 反射回来的电子却起加速作用，'
     '两者方向相反，于是形成与阴极电流方向相反的反向电流。')
body('三股电流叠在一起，实测的伏安特性曲线在截止电压附近就不再是陡直地降为零，而是拖着一段'
     '平缓的“尾巴”，电流为零的位置所对应的电压往往并不是真正的截止电位，而是偏小一些。为了修正'
     '这一点，讲义给出的补偿法是：先调电压使外电路电流为零，保持这个电压不变，用遮光罩挡掉汞灯'
     '光源，此时测到的电流 I₁ 就近似等于该电压下的暗电流与本底电流之和；然后让光照回来，重新'
     '调节电压，使电流表的示数刚好等于 I₁，这时对应的反向电压才可以作为截止电位。这样处理之后，'
     '暗电流和本底电流对结果的影响就被扣掉了。')

# ---------------------------------------------------------------- 步骤
heading('实验内容与步骤', '10%', NOTE_STEPS)
body('1．测试前准备。把汞灯暗箱和光电管暗箱的遮光罩都盖好、打开汞灯电源；把汞灯暗箱的光输出口'
     '正对光电管暗箱的光输入口，调节两者相距约 40 cm 并保持不动；用专用连接线按红接红、黑接黑'
     '把电压线接好，打开实验仪电源预热 20～30 分钟。预热充分后才能调零：调零前必须先把光电管暗箱'
     '微电流输出端与实验仪微电流输入端之间的高频匹配电缆断开，把电流量程开关置于准备使用的档位，'
     '旋转“电流调零”旋钮使电流显示为 000.0，调好后再把电缆接回。测量中每换一次量程都必须重新'
     '调零，否则示数会带着一个非零的本底。')
body('2．测伏安特性曲线。功能键置于“手动”档，先取 435.8 nm 谱线、光阑 2 mm，电流量程用'
     '10⁻¹³ A 档；从 −4 V 开始用电压调节按钮逐点升高到 +30 V，每一点同时记下电压 U_AK 与对应的'
     '电流 I，填入表 1。电流为零的那一点附近要多取几个点、把那个电压找准，电流达到饱和以后还要'
     '再补测几组数据。再换 546.1 nm 谱线、光阑 4 mm、量程 10⁻¹² A 档，按同样的电压顺序重复'
     '测量一次。')
body('3．测各谱线的截止电压。光阑保持 2 mm，依次换上 365.0、404.7、435.8、546.1、577.0 nm '
     '五片滤色片，每换一片都确认它卡到位、光路没有漏光；对每一波长用零电流法找出使电流恰好降为'
     '零的那个电压，重复测量三次，记入表 3。')
body('4．测饱和电流与光强的关系。把电压稳定在 +30 V，在 435.8 nm 与 546.1 nm 两条谱线下依次'
     '换上 2 mm、4 mm、8 mm 的光阑孔，量程分别改用 10⁻¹³、10⁻¹²、10⁻¹¹ A 档，换档后重新调零，'
     '分别读出各光阑下的饱和电流 I_M，记入表 2。')
body('5．实验结束。测量完毕先把遮光罩盖好，把滤色片旋到堵住光口的位置，按“复位”键使电压归零，'
     '再关闭实验仪电源和汞灯电源；汞灯关闭后不能马上重新开启，必须等灯丝充分冷却，否则会影响'
     '灯管寿命。')

# ---------------------------------------------------------------- 原始数据照片
heading('有教师签字的原始数据记录照片（请竖排粘贴）', '10%')
figure(GEN + r'\data_photo.jpg', 12.40, None)

# ---------------------------------------------------------------- 数据处理
heading('数据处理及结果', '20%', NOTE_DATA)
body('表 1 是全部测量记录的汇总，435.8 nm（Φ=2 mm）与 546.1 nm（Φ=4 mm）两条谱线各测了'
     '22 个电压点的完整伏安特性，把它们描在坐标纸上即得图 4 的两条曲线；由曲线的上升沿可以读出'
     '截止电压的位置，由饱和段可以读出饱和电流 I_M。')
body('表 2 用来检验饱和光电流与入射光强是否成正比。光强与光阑孔的面积成正比，而面积又与孔径的'
     '平方 Φ² 成正比，所以只要把 I_M 对 Φ² 作图（图 5），若各点落在一条过原点的直线上，就说明'
     'I_M 与入射光强成正比。')
body('表 3 是对 h 作定量测量的依据。同一波长下三次测得的截止电压取算术平均值作为该波长的 U_s，'
     '再配合五条谱线已知的频率 ν 作 U_s～ν 直线（图 6），由直线的斜率 K 算出普朗克常量 h，'
     '并与公认值 6.626×10⁻³⁴ J·s 比较求相对误差。')

caption('表 1  光电管的 U_AK～I 关系（I 的单位为 10⁻¹¹ A）')
W1 = [1150, 1150] + [750] * 8
t1 = new_table(18, 10, W1)
for blk in range(3):
    r0 = blk * 6
    t1.cell(r0, 0).merge(t1.cell(r0 + 1, 0))
    t1.cell(r0, 1).merge(t1.cell(r0 + 1, 1))
    t1.cell(r0, 2).merge(t1.cell(r0, 9))
for r in range(18):
    for c in range(10):
        cell_setup(t1.cell(r, c), W1[c])
groups = [(1, 8), (9, 16), (17, 23)]
for blk, (g0, g1) in enumerate(groups):
    r0 = blk * 6
    put_lines(t1.cell(r0, 0), ['波长', '光阑'])
    put_lines(t1.cell(r0, 1), ['电压', '电流'])
    put(t1.cell(r0, 2), '测量数组')
    for k in range(8):
        put(t1.cell(r0 + 1, 2 + k), str(g0 + k) if g0 + k <= g1 else '')
    put(t1.cell(r0 + 2, 0), '435.8 nm')
    put(t1.cell(r0 + 2, 1), 'U_AK (V)')
    put(t1.cell(r0 + 3, 0), '2 mm')
    put(t1.cell(r0 + 3, 1), 'I')
    put(t1.cell(r0 + 4, 0), '546.1 nm')
    put(t1.cell(r0 + 4, 1), 'U_AK (V)')
    put(t1.cell(r0 + 5, 0), '4 mm')
    put(t1.cell(r0 + 5, 1), 'I')
    for k in range(8):
        idx = blk * 8 + k
        if idx >= 22:
            continue
        u = T1[0]['U_AK_V'][idx]
        i1 = T1[0]['I'][idx]
        i2 = T1[1]['I'][idx]
        put(t1.cell(r0 + 2, 2 + k), ('−%d' % -u) if u < 0 else str(u))
        put(t1.cell(r0 + 3, 2 + k), '%.1f' % i1)
        put(t1.cell(r0 + 4, 2 + k), ('−%d' % -u) if u < 0 else str(u))
        put(t1.cell(r0 + 5, 2 + k), '%.1f' % i2)

figure(GEN + r'\figures\fig_va.png', 14.30, '图 4  光电管的伏安特性曲线')

caption('表 2  饱和电流 I_M 与光阑孔面积（光强）的关系（U_AK = 30 V）')
W2 = [1500, 1700, 1700, 1700, 1700]
t2 = new_table(6, 5, W2)
for r in range(6):
    for c in range(5):
        cell_setup(t2.cell(r, c), W2[c])
t2.cell(0, 0).merge(t2.cell(1, 0))
t2.cell(0, 1).merge(t2.cell(1, 1))
t2.cell(0, 2).merge(t2.cell(0, 4))
t2.cell(2, 0).merge(t2.cell(3, 0))
t2.cell(4, 0).merge(t2.cell(5, 0))
put_lines(t2.cell(0, 0), ['波长'])
put_lines(t2.cell(0, 1), ['光阑', '电流'])
put(t2.cell(0, 2), '测量数组')
for k in range(3):
    put(t2.cell(1, 2 + k), str(k + 1))
for gi, ser in enumerate(T2['series']):
    rr = 2 + gi * 2
    put(t2.cell(rr, 0), '%.1f nm' % ser['lambda_nm'])
    put(t2.cell(rr, 1), '光阑孔 Φ')
    put(t2.cell(rr + 1, 1), 'I（10⁻¹¹ A）')
    for k in range(3):
        put(t2.cell(rr, 2 + k), '%d mm' % ser['phi_mm'][k])
        put(t2.cell(rr + 1, 2 + k), '%.1f' % ser['I_M'][k])

figure(GEN + r'\figures\fig_ip.png', 14.30, '图 5  饱和电流 I_M 与光阑孔面积 Φ² 的关系')

caption('表 3  截止电压 U_s 与入射光频率 ν 的关系（Φ = 2 mm）')
W3 = [1750, 450, 1220, 1220, 1220, 1220, 1220]
t3 = new_table(6, 7, W3)
for r in range(6):
    for c in range(7):
        cell_setup(t3.cell(r, c), W3[c])
t3.cell(0, 0).merge(t3.cell(0, 1))
t3.cell(1, 0).merge(t3.cell(1, 1))
t3.cell(2, 0).merge(t3.cell(4, 0))
t3.cell(5, 0).merge(t3.cell(5, 1))
put(t3.cell(0, 0), '波长 λ（nm）')
put(t3.cell(1, 0), '频率 ν（10¹⁴ Hz）')
put_lines(t3.cell(2, 0), ['截止电压', 'U_s（V）'])
put(t3.cell(5, 0), 'U_s 平均值（V）')
for rr in range(3):
    put(t3.cell(2 + rr, 1), str(rr + 1))
for k in range(5):
    put(t3.cell(0, 2 + k), '%.1f' % T3['lambda_nm'][k])
    put(t3.cell(1, 2 + k), '%.3f' % T3['nu_1014Hz'][k])
    for rr in range(3):
        v = T3['U0_runs'][rr][k]
        put(t3.cell(2 + rr, 2 + k), '−%.3f' % -v)
    put(t3.cell(5, 2 + k), '−%.3f' % -T3['U0_avg_V'][k])
figure(GEN + r'\figures\fig_u0nu.png', 14.30, '图 6  截止电压 U_s 与入射光频率 ν 的关系')

# ---------------- 计算
K14 = FIT['slope_a14_V_per_1e14Hz']
K = FIT['slope_K_Vs']
H = FIT['h_Js']
B = FIT['intercept_b_V']
R = FIT['r']
R2 = FIT['r2']
ERR = FIT['rel_err_pct']

nu = D['u0_avg']['nu_1014Hz']
us = D['u0_avg']['U_s_V']
n = len(nu)
resid, sum_d2 = [], 0.0
mnu = sum(nu) / n
for x, y in zip(nu, us):
    resid.append(y - (K14 * x + B))
    sum_d2 += (x - mnu) ** 2
s2 = sum(rr * rr for rr in resid) / (n - 2)
sigma_K14 = (s2 / sum_d2) ** 0.5
sigma_K = sigma_K14 * 1e-14
sigma_h = 1.602e-19 * sigma_K
nu0 = -B / K14
lam0 = 2.99792458e8 / (nu0 * 1e14) * 1e9
A_s = -B

body('1．截止电压的平均值。由表 3 末行，365.0 nm 处 U_s = 1.504 V，404.7 nm 处为 0.921 V，'
     '435.8 nm 处为 0.641 V，546.1 nm 处为 0.200 V，577.0 nm 处为 0.175 V，三次测量的标准差'
     '分别为 0.013、0.005、0.015、0.009、0.006 V，重复性尚好。')
body('2．线性拟合。以 ν 为横坐标（单位 10¹⁴ Hz）、U_s 为纵坐标作最小二乘直线，得')
formula([('U', 'i'), ('s', 'sub'), (' = ', 'u'), ('%.4f' % K14, 'u'), ('ν', 'i'),
         (' − ', 'u'), ('%.3f' % A_s, 'u')])
body('其相关系数 r = %.4f（R² = %.4f），斜率 K = %.4f×10⁻¹⁴ V·s = %.4f×10⁻¹⁵ V·s，'
     '截距 b = −%.3f V。' % (R, R2, K14, K * 1e15, A_s))
body('3．普朗克常量。由 h = eK 得')
formula([('h', 'i'), (' = ', 'u'), ('1.602×10⁻¹⁹ C × %.4f×10⁻¹⁵ V·s = %.3f×10⁻³⁴ J·s'
                              % (K * 1e15, H * 1e34), 'u')])
body('4．相对误差。')
formula([('E', 'i'), (' = ', 'u'), ('|%.3f − 6.626| / 6.626 × 100%% = %.2f%%'
                                   % (H * 1e34, ERR), 'u')])
body('5．不确定度。由残差求得斜率的标准不确定度 u(K) = %.3f×10⁻¹⁴ V·s，相应'
     ' u(h) = e·u(K) = %.2f×10⁻³⁴ J·s，故测量结果可写为 h = (%.2f ± %.2f)×10⁻³⁴ J·s。'
     % (sigma_K14, sigma_h * 1e34, H * 1e34, sigma_h * 1e34))
body('6．逸出功与红限。由截距 b = −A_s/e 得该光电管阴极的逸出功 A_s = %.3f eV；令 U_s = 0 '
     '得红限频率 ν₀ = %.3f×10¹⁴ Hz，对应波长约 %.0f nm，与实验中所用最长波长 577.0 nm 很'
     '接近，说明该光电管的阴极材料对可见光的长波段已接近截止（见表 3 中 546.1 nm 与 577.0 nm '
     '两点的截止电压已降到 0.2 V 以下）。' % (A_s, nu0, lam0))
body('7．饱和电流与光强。由表 2 数据算得归一化比值：435.8 nm 为 1∶%.2f∶%.2f，546.1 nm 为'
     ' 1∶%.2f∶%.2f，而光阑面积之比为 1∶4∶16，两者相差约 8%%～11%%，在实验精度内可以认为'
     '饱和光电流与入射光强成正比，这也正是光子假说所预言的。'
     % (CHK[0]['normalized_I_M'][1], CHK[0]['normalized_I_M'][2],
        CHK[1]['normalized_I_M'][1], CHK[1]['normalized_I_M'][2]))

# ---------------------------------------------------------------- 体会
heading('分析及体会', '20%', NOTE_EXP)
body('这次实验里，占去时间最多的其实不是测数据，而是让仪器先“听话”。调零这一步看着简单，'
     '却是我出错最多的地方：第一遍我没注意面板上的提示，直接带着高频匹配电缆就转调零旋钮，示数'
     '怎么都压不到零，后来断开电缆再调，一下子就好了，这个细节让我记住了“先断线、后调零”的'
     '顺序。零电流点是第二个坎，示数在 −1 V 附近跳几下就归零，再往负走又出来一点负值，我一开始'
     '连续读了好几个 0.0，回头一比较才发现偏了零点几伏，只能重新回来细找，可见示数小并不等于'
     '读数容易。测到 577.0 nm 时电流本身就很小，量程换到更灵敏的档位以后读数更飘，我又按规程'
     '重新调了一次零，数据才稳下来。还有两件小事印象很深：换滤色片时我下意识想用手指捏住镜片'
     '正面，被提醒后改成捏边框；收尾时同学急着重新开汞灯，被老师拦住要等灯丝冷却，说反复冷热'
     '会缩短寿命。')
body('回头看数据，我最在意的不是 h 最后差了多少，而是曲线在截止电压附近那一段为什么那么“软”。'
     '照理说电流应该在某个电压处陡直地掉到零，实际却是慢慢平缓地爬过去，这正好印证了原理里讲的'
     '那三股干扰电流，尤其是阳极反向电流——它和阴极电流方向相反，在截止电压附近占的比例越来越大，'
     '把真实的“拐点”抹平了。这也能解释零电流法为什么会让 U_s 偏小：电流示数为零的时候，阴极'
     '其实还在发射电子，只是它们正好被反向电流和暗电流抵消掉，真正的截止电位要更负一些。此外，'
     '读数本身有偶然误差，电压靠按钮一点点加，分辨率有限；546.1 nm 那一组在 −3 V 处的读数反而'
     '比 −4 V 处还小，大概是示数在末位跳动时被记录取整造成的，这类反常点也提醒我不能见到数字就'
     '照抄，当场判断一下是否合理会省掉很多返工；U_s～ν 直线只有五个点，其中一个点'
     '偏一点，斜率就会跟着变；光阑如果没和光路对正，实际光强与孔径的标称关系就有偏差；实验中途'
     '阴极出现轻微疲劳，暗电流也会缓慢漂移。这些加在一起，算出来的 h 偏几个百分点是很正常的。')
body('做完这个实验，我对“光电效应能干什么”才算有了切身感受。光电倍增管就是把它做到了极致，'
     '用一串打拿极把每个光电子逐级倍增，能测到单个光子的信号，粒子物理和高能物理里的闪烁探测器'
     '靠的就是它；光电池和太阳能电池则是它的逆过程，光子把电子激发到导带，靠内建电场把电子与'
     '空穴分开，从而把光能变成电能；光电开关、光电传感器只要求“有光没光”的二值判断，结构最'
     '简单，却无处不在。我们机器人工程专业用得很多的编码器，盘片上刻着一圈透光和不透光的狭缝，'
     '光穿过狭缝落到光电管上，盘一转电流就随明暗交替，位置和转速就都测出来了；手机摄像头里的'
     'CMOS 像素，本质上也是一堆微型光电二极管在把光子变成电荷，只不过它要的是成像而不是测电流。'
     '想到爱因斯坦 1905 年提出光子假说、1921 年因此获得诺贝尔物理学奖，而密立根 1916 年用精密的'
     '截止电压测量验证了他的方程、随后在 1923 年因测电子电荷获奖，这一段“理论与实验互相咬合”的'
     '历史特别打动我。')
body('顺着这个思路我还多想了一层：既然 h 可以由截止电压随频率变化的斜率求出，那么反过来，'
     '如果已经有了较准的 h，用发光二极管做“反向”实验也能粗略把它测出来。LED 发光是电子与空穴'
     '复合放光，光子能量近似等于材料的禁带宽度，而禁带宽度又与开启电压成正比，所以只要测出几种'
     '不同颜色 LED 的开启电压和发光波长，把电子的电荷乘上开启电压再乘上波长、除以光速，就能估出'
     ' h 的量级。这个想法虽然没有做过，但它让我明白：光电效应并不是一个孤立的定律，它把光的'
     '频率、电子的电荷和一个基本常量串在了同一条直线上，谁被测量得足够准，另外两个就能反推出来，'
     '这大概就是基础常数测量最迷人的地方。')
body('说到底，这个实验让我收获的不只是一个 h 的数值，而是一整套“怎么把公式变成可读的数据”的'
     '经验：操作上要守规程，调零、断线、换档、遮光这些动作一步都不能省；读数据时要沉住气，'
     '尤其是零电流点这种小量，多看一眼往往就能救回一组数据；处理数据时要明白误差从哪里来，'
     '不能把偏离直线的原因一律推给“仪器不准”。我以前总觉得物理实验就是把数代进公式，这次才'
     '体会到，真正费功夫的是判断“这条曲线为什么长成这样”。')

# ---------------------------------------------------------------- 思考题
p = new_p(keep_next=True, space_before=12)
mk_run(p, '思考题', bold=True, size=12)
body('【题目 1】实验中电流为零的点所对应的电压是否为要测的遏止电压？为什么？', indent=False)
body('【解答】严格说不是，只能算近似。外电路电流为零时，阴极其实仍在发射光电子，只是这部分'
     '电流恰好被方向相反的阳极反向电流以及暗电流、本底电流抵消掉了，所以零电流点对应的反向电压'
     '绝对值比真正的截止电位要小一些。只有当这几股干扰电流都远小于光电流时，两者才近似相等，'
     '这正是零电流法能用的前提。', indent=False)
body('【题目 2】反向电流的来源是什么？暗电流的来源是什么？', indent=False)
body('【解答】反向电流来自两处：一是制作光电管时阳极表面溅上了阴极材料，光照射到阳极上，'
     '阳极自身也逸出光电子；二是阴极逸出的部分光电子被阳极反射回来。加反向电压时，电场对阴极'
     '电子是减速，对阳极发出和反射的电子却是加速，于是形成反向电流。暗电流则是无光照时的微弱'
     '电流，来自阴极的热电子发射和绝缘不良造成的漏电流。', indent=False)
body('【题目 3】更换滤色片时应注意什么？能不能直接使高压汞灯照射光电管？为什么？', indent=False)
body('【解答】换片前先盖好遮光罩挡住光路；滤色片的光学面不能用手摸，油污汗渍会改变透光率甚至'
     '损伤膜层，取放时捏住边框；装好后确认卡到位并与光轴同心。不能让汞灯白光直接照光电管：'
     '各谱线同时打在阴极上，得到的是多种频率混合的电流，伏安特性曲线失去单一频率的含义，'
     '截止电位无从确定；强紫外光还会使阴极疲劳、灵敏度下降。', indent=False)

# ---------------------------------------------------------------- 超星截图
heading('超星平台本实验在线练习得分截图（请竖排粘贴）', '5%')
new_p(keep_next=True)
frame = doc.add_table(rows=1, cols=1)
frame.alignment = WD_TABLE_ALIGNMENT.CENTER
frame.autofit = False
frame.columns[0].width = tw(8300)
frame.cell(0, 0).width = tw(8300)
tcPr = frame.cell(0, 0)._tc.get_or_add_tcPr()
b = OxmlElement('w:tcBorders')
for edge in ('top', 'left', 'bottom', 'right'):
    e = OxmlElement('w:' + edge)
    e.set(qn('w:val'), 'nil')
    b.append(e)
tcPr.append(b)
cell = frame.cell(0, 0)
cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
p0 = cell.paragraphs[0]
p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
pf = p0.paragraph_format
pf.first_line_indent = Pt(0)
pf.space_before = Pt(6)
pf.space_after = Pt(6)
p0.add_run().add_picture(SHOT, width=Cm(8.20))

for _t in doc.tables:
    kill_vmerge_inner_lines(_t)

FTTEXT = '光电效应的研究'
for _sec in doc.sections:
    for _p in _sec.footer.paragraphs:
        for _r in _p.runs:
            if '长度测量' in _r.text:
                _r.text = _r.text.replace('长度测量', FTTEXT)
doc.save(OUT)

# ---------------------------------------------------------------- verify
import io

chk = Document(OUT)
buf = io.StringIO()


def P(s):
    buf.write(str(s) + '\n')


P('saved: %s' % OUT)
P('paragraphs: %d tables: %d images: %d' % (len(chk.paragraphs), len(chk.tables),
                                            len(chk.inline_shapes)))
s0 = chk.sections[0]
P('page: %s x %s' % (s0.page_width, s0.page_height))
P('margins L/R/T/B: %s %s %s %s' % (s0.left_margin, s0.right_margin,
                                    s0.top_margin, s0.bottom_margin))
P('header: %r' % s0.header.paragraphs[0].text)
P('footer: %r' % s0.footer.paragraphs[0].text)
txt = '\n'.join(p.text for p in chk.paragraphs)
P('chars(no space/nl): %d' % len(txt.replace(' ', '').replace('\n', '')))
for key in ('热膨胀', '长度测量', 'None', '[[F', '=== '):
    P('contains %s: %s' % (key, key in txt))
P('')
P('=== TABLE WIDTHS (twips) ===')
for i, t in enumerate(chk.tables):
    widths = [c.width.twips if c.width else None for c in t.rows[0].cells]
    P('table%d rows=%d cols=%d widths=%s sum=%s' % (
        i, len(t.rows), len(t.columns), widths[:6],
        sum(w for w in widths if w)))
P('')
P('=== INLINE SHAPES ===')
for sh in chk.inline_shapes:
    P('%s  %.2fcm x %.2fcm' % (sh.type, sh.width.cm, sh.height.cm))
P('')
P('=== PARAGRAPHS ===')
for i, p in enumerate(chk.paragraphs):
    sizes = sorted({(r.font.size.pt if r.font.size else None) for r in p.runs})
    P('[%03d] %s ind=%s | %s' % (
        i, sizes,
        p.paragraph_format.first_line_indent.pt if p.paragraph_format.first_line_indent else 0,
        p.text[:100]))
open(GEN + r'\verify_layout.txt', 'w', encoding='utf-8').write(buf.getvalue())
print('verify written', len(buf.getvalue()))
