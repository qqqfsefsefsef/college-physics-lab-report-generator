# -*- coding: utf-8 -*-
"""
钨的逸出功测定 —— 读数整理 / 最小二乘拟合 / Pillow 手绘图（幂等，重跑结果一致）

数据来源：04_生成过程_脚本图表\\src_new.png（学生手写原始数据页，3072x4096）
输出：
    data_tungsten.json
    read_report.txt
    figures_tungsten\\fig_w1.png / fig_w2.png / fig_w3.png   (1725x1100)
"""
import json
import math
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(BASE, 'figures_tungsten')
JSON_PATH = os.path.join(BASE, 'data_tungsten.json')
REPORT_PATH = os.path.join(BASE, 'read_report.txt')

FONT_R = r'C:\Windows\Fonts\msyh.ttc'
FONT_B = r'C:\Windows\Fonts\msyhbd.ttc'

K_BOLTZ = 1.3806505e-23        # J/K
E_CHARGE = 1.602e-19           # C
PHI_ACCEPT_EV = 4.54           # eV 公认值

# ---------------------------------------------------------------- 原始读数 ---
U_A = [25, 36, 49, 64, 81, 100, 121, 144]                         # V
I_F = [0.600, 0.625, 0.650, 0.675, 0.700, 0.725, 0.750, 0.775]    # A
# 表 1：阳极电流 I_a / uA（行 = I_f，列 = U_a）
TAB1 = [
    [23,   23,   24,   24,   25,   26,   26,   28],
    [43,   44,   44,   45,   46,   48,   48,   50],
    [78,   80,   81,   83,   84,   86,   87,   88],
    [139,  140,  142,  143,  152,  152,  153,  157],
    [237,  242,  244,  249,  255,  260,  262,  268],
    [393,  405,  410,  420,  425,  434,  447,  431],
    [645,  664,  666,  682,  694,  707,  725,  728],
    [1030, 1050, 1071, 1081, 1112, 1129, 1144, 1162],
]

SQRU = [5, 6, 7, 8, 9, 10, 11, 12]                   # sqrt(U_a)
T2 = [1.88, 1.92, 1.96, 2.00, 2.04, 2.08, 2.12]      # 表2 行标签 T/10^3K
# 表 2：lg I_a（行 = T，列 = sqrt(U_a)）
TAB2 = [
    [1.36, 1.36, 1.38, 1.38, 1.39, 1.41, 1.41, 1.44],
    [1.63, 1.64, 1.64, 1.65, 1.66, 1.68, 1.68, 1.70],
    [1.89, 1.90, 1.91, 1.92, 1.92, 1.93, 1.94, 1.94],
    [2.14, 2.15, 2.15, 2.16, 2.18, 2.18, 2.18, 2.20],
    [2.37, 2.38, 2.39, 2.40, 2.41, 2.42, 2.42, 2.43],
    [2.59, 2.61, 2.61, 2.62, 2.63, 2.63, 2.65, 2.65],
    [2.81, 2.82, 2.82, 2.83, 2.84, 2.85, 2.86, 2.86],
]
# 表 2 印刷网格之外手写补写的一行，按 T = 2.16 x 10^3 K 收录
TAB2_ROW_216 = [3.01, 3.02, 3.03, 3.03, 3.05, 3.05, 3.06, 3.07]
T216 = 2.16

# 表 3
T3 = [1.88, 1.92, 1.96, 2.00, 2.04, 2.08, 2.12, 2.16]       # T/10^3K
T3_INV = [0.53, 0.52, 0.51, 0.50, 0.49, 0.48, 0.47, 0.46]   # 1/T / 10^-3 K^-1
T3_LGI = [1.29, 1.57, 1.85, 2.09, 2.32, 2.55, 2.78, 2.97]   # lg I_s
T3_LGR = [0.75, 1.01, 1.27, 1.50, 1.71, 1.92, 2.12, 2.30]   # lg(I_s/T^2)，T 以 10^3K 计

AMBIGUOUS = [
    ("表1 / I_f=0.600 整行（U_a=25..144 V，共 8 格）",
     "8 格均被铅笔反复涂改，笔画前后各带圆形涂抹。最终认定 23,23,24,24,25,26,26,28 uA。"
     "佐证：表 2 第一行 lg I_a=1.36,1.36,1.38,1.38,1.39,1.41,1.41,1.44，与 "
     "lg(23)=1.362 / lg(24)=1.380 / lg(25)=1.398 / lg(26)=1.415 / lg(28)=1.447 逐一吻合；"
     "若按看上去的“230/240/250”计，lg 会整体高 1.000，与表 2 直接矛盾。"),
    ("表1 / I_f=0.700, U_a=36 V",
     "原写数字被划掉，右上角小字改写为 242；取 242（表 2 对应格 2.38 = lg(242) 亦支持）。"),
    ("表1 / I_f=0.675, U_a=100 V",
     "格内有划改痕迹，最终读作 152（与同行 81 V 的 152 连续，且表 2 对应格 1.92 相当）。"),
    ("表1 / I_f=0.725, U_a=144 V",
     "读作 431（末笔为竖划‘1’，非‘7’）。但表 2 同一位置（T=2.08, √U_a=12）写的是 2.65，"
     "而 lg(431)=2.634 应为 2.63 —— 两表在此格不自洽，判为抄录笔误：本报告表 1 保留 431、"
     "表 2 保留 2.65，图 2 用表 2 数据。"),
    ("表2 / T=2.00, √U_a=5",
     "先写 2.14，随后整段被粗横线划掉并涂抹；最终值取 2.14"
     "（该行 2.14,2.15,2.15,2.16,2.18,2.18,2.18,2.20 单调、与表 1 的 139 一致）。"),
    ("表2 / T=1.88 整行 与 T=2.12 行 U_a=144 格",
     "数字尾端均带一个小圆点/涂抹（本例读作 1.44、2.86），按末位数字取值，不影响小数第二位。"),
    ("表3 / lgI 行第 1 格（T=1.88）",
     "写作 1.29，末位 9 上有明显铅笔覆盖，亦可读作 1.30；本表取 1.29。"
     "自洽性：表 2 外推得 lg I_s(1.88)=1.303，且第 4 行 0.75+2lg(1.88)=1.298，"
     "两种取法只差 0.01，对斜率影响 < 0.5%。"),
    ("表3 / 第 4 行最右格（T=2.16）",
     "写作“2.3”，只有一位小数（其余格均为两位），按 2.30 收录。"),
    ("表3 / 第 4 行行标题的字形",
     "印刷体为“lgI（I/T²）”，括号内分子是大写字母 I（与“lgI”中的 I 同一字形），不是数字 1；"
     "结合本表标题“表 3  lg（I_s/T²）~1/T 数据表”及数值关系，判定该行为 lg(I_s/T²)。"),
]


# ------------------------------------------------------------------ 拟合 ---
def linfit(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    m = sxy / sxx
    b = my - m * mx
    yhat = [m * x + b for x in xs]
    ss_res = sum((y - yh) ** 2 for y, yh in zip(ys, yhat))
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1.0 - ss_res / ss_tot
    r = math.copysign(math.sqrt(max(r2, 0.0)), m)
    dof = n - 2
    se = math.sqrt(ss_res / dof) if dof > 0 else 0.0
    return {
        'n': n, 'slope': m, 'intercept': b, 'r': r, 'r2': r2,
        's_resid': se,
        'se_slope': se / math.sqrt(sxx),
        'se_intercept': se * math.sqrt(1.0 / n + mx * mx / sxx),
        'mean_x': mx, 'mean_y': my,
    }


def rnd(v, nd=12):
    """按 12 位有效数字保留（round 会因量级过小而截成 0，如 7.0e-19）。"""
    v = float(v)
    if v == 0.0:
        return 0.0
    return float('%.12g' % v)


TAB1_LG = [[math.log10(v) for v in row] for row in TAB1]

FITS_T2 = []
for t, row in zip(T2, TAB2):
    f = linfit(SQRU, row)
    FITS_T2.append({'T_1000K': t, **{k: rnd(v) for k, v in f.items()}})
LG_IS_FIT = [f['intercept'] for f in FITS_T2]
FIT_T216 = linfit(SQRU, TAB2_ROW_216)
LG_IS_ALL = LG_IS_FIT + [FIT_T216['intercept']]

FIT_T3 = linfit(T3_INV, T3_LGR)
M_PLOT = FIT_T3['slope']
M_TRUE = M_PLOT * 1e3
PHI_J = 2.303 * K_BOLTZ * abs(M_TRUE)
PHI_EV = PHI_J / E_CHARGE
REL_ERR = (PHI_EV - PHI_ACCEPT_EV) / PHI_ACCEPT_EV * 100.0
ABS_ERR = PHI_EV - PHI_ACCEPT_EV

FIT_T3_EXACT = linfit([1.0 / t for t in T3], T3_LGR)
PHI_EV_EXACT = 2.303 * K_BOLTZ * abs(FIT_T3_EXACT['slope'] * 1e3) / E_CHARGE

Y_RECOMP = [lg - 2.0 * math.log10(t * 1e3) for lg, t in zip(LG_IS_FIT, T3[:len(LG_IS_FIT)])]
FIT_T3_RECOMP = linfit(T3_INV[:len(Y_RECOMP)], Y_RECOMP)
PHI_EV_RECOMP = 2.303 * K_BOLTZ * abs(FIT_T3_RECOMP['slope'] * 1e3) / E_CHARGE

LG_T_TRUE = [2.0 * math.log10(t * 1e3) for t in T3]
LG_T_1E3 = [2.0 * math.log10(t) for t in T3]
OFFSET_CHECK = [a - b for a, b in zip(T3_LGI, T3_LGR)]
OFFSET_MEAN = sum(OFFSET_CHECK) / len(OFFSET_CHECK)
FIT_OFFSET6 = linfit(T3_INV, [y - 6.0 for y in T3_LGR])

CHECK_T12 = []
for i, (row1, row2) in enumerate(zip(TAB1_LG, TAB2)):
    d = [abs(a - b) for a, b in zip(row1, row2)]
    CHECK_T12.append({'T_1000K': T2[i], 'max_abs_diff_lg': rnd(max(d)),
                      'mean_abs_diff_lg': rnd(sum(d) / len(d))})
ROW216_LG = [math.log10(v) for v in TAB1[-1]]
CHECK_216 = {'T_1000K': T216,
             'lg_of_table1_row8': [rnd(v, 6) for v in ROW216_LG],
             'handwritten_row': TAB2_ROW_216,
             'max_abs_diff_lg': rnd(max(abs(a - b) for a, b in zip(ROW216_LG, TAB2_ROW_216)))}


# ------------------------------------------------------------------ JSON ---
data = {
    'meta': {
        'experiment': '钨的逸出功测定（理查森-杜什曼公式 lg(I_s/T^2) = lgA - e*phi/(2.303k) * 1/T）',
        'source_image': r'04_生成过程_脚本图表\src_new.png',
        'source_image_size': [3072, 4096],
        'constants': {'k_J_per_K': K_BOLTZ, 'e_C': E_CHARGE,
                      'phi_accepted_eV': PHI_ACCEPT_EV,
                      'T_calibration': 'T = 920.0 + 1600*I_f  (T in K, I_f in A)'},
        'units': {'table1': 'I_a/uA, U_a/V, I_f/A',
                  'table2': 'lg I_a, sqrt(U_a), T/1e3 K',
                  'table3': '1/T(1e-3 K^-1), lg I_s, lg(I_s/T^2)'},
        'note_row_T216': ('表 2 印刷网格只有 7 行（1.88~2.12）。网格底线之外、表 3 标题之上手写着 '
                          '3.01 3.02 3.03 3.03 3.05 3.05 3.06 3.07，与表 1 第 8 行 '
                          'I_f=0.775A（I_a=1030..1162 uA）取对数逐一吻合，判定为 T=2.16x10^3K '
                          '一行的 lg I_a（学生漏写行标签），而不是外推截距 lg I_s。'),
    },
    'table1': {'u_a_V': U_A, 'i_f_A': I_F, 'i_a_uA': TAB1,
               'lg_i_a_computed': [[rnd(v, 6) for v in row] for row in TAB1_LG]},
    'table2': {'sqrt_u_a': SQRU, 'T_1000K': T2, 'lg_i_a': TAB2,
               'lg_i_a_row_T216_extra': TAB2_ROW_216},
    'table2_fits': FITS_T2,
    'table2_fit_T216_extra': {k: rnd(v) for k, v in FIT_T216.items()},
    'lg_is_from_extrapolation': [rnd(v) for v in LG_IS_ALL],
    'table3': {'T_1000K': T3, 'inv_T_1e3_per_K': T3_INV,
               'lg_i': T3_LGI, 'lg_is_over_T2_written': T3_LGR},
    'table3_fit': {k: rnd(v) for k, v in FIT_T3.items()},
    'escape_work': {
        'slope_plot_m': rnd(M_PLOT),
        'slope_true_m_per_K': rnd(M_TRUE),
        'phi_J': rnd(PHI_J),
        'phi_eV': rnd(PHI_EV),
        'accepted_eV': PHI_ACCEPT_EV,
        'abs_error_eV': rnd(ABS_ERR),
        'relative_error_percent': rnd(REL_ERR),
        'formula': 'e*phi = 2.303 * k * |m_true|,  m_true = m_plot * 1e3',
    },
    'variants': {
        'exact_inv_T': {k: rnd(v) for k, v in FIT_T3_EXACT.items()},
        'exact_inv_T_phi_eV': rnd(PHI_EV_EXACT),
        'recomputed_lg_is': {k: rnd(v) for k, v in FIT_T3_RECOMP.items()},
        'recomputed_lg_is_phi_eV': rnd(PHI_EV_RECOMP),
    },
    'checks': {
        'table1_lg_vs_table2': CHECK_T12,
        'row_T216_matches_table1_row8': CHECK_216,
        'offset_row3_minus_row4': [rnd(v, 4) for v in OFFSET_CHECK],
        'offset_mean': rnd(OFFSET_MEAN, 6),
        'two_lg_T_true': [rnd(v, 6) for v in LG_T_TRUE],
        'two_lg_T_using_1e3': [rnd(v, 6) for v in LG_T_1E3],
        'shifted_by_6_slope': rnd(FIT_OFFSET6['slope']),
        'shifted_by_6_slope_identical': abs(FIT_OFFSET6['slope'] - FIT_T3['slope']) < 1e-12,
        'conclusion_offset': ('第 4 行 = lgI - 2lg(T/1e3)，即比真实的 lg(I_s/T^2) 系统性高 6.000'
                              '（= 2lg1000）；整体平移不改变最小二乘斜率，eφ 不受影响。'),
    },
    'ambiguous_cells': [{'cell': c, 'note': n} for c, n in AMBIGUOUS],
}
os.makedirs(FIGDIR, exist_ok=True)
with open(JSON_PATH, 'w', encoding='utf-8') as fh:
    json.dump(data, fh, ensure_ascii=False, indent=2)
    fh.write('\n')

# --------------------------------------------------------------- 绘图基础 ---
SCALE = 2
W, H = 1725, 1100

C_BLACK = (0, 0, 0)
C_GRID = (198, 198, 198)
PALETTE = [
    (20, 20, 20), (198, 40, 40), (30, 90, 175), (15, 130, 85),
    (172, 96, 12), (128, 46, 148), (0, 122, 142), (108, 108, 108),
]
SHAPES = ['o', 's', '^', 'D', 'v', '+', 'x', 'h']


def px(v):
    return int(round(v * SCALE))


def get_font(size, bold=False):
    path = FONT_B if (bold and os.path.exists(FONT_B)) else FONT_R
    return ImageFont.truetype(path, int(round(size * SCALE)))


def parse_rich(s):
    """mini-markup: ~x~ 下标, ^x^ 上标."""
    if not isinstance(s, str):
        return s
    out, buf, mode, i = [], '', 'n', 0
    while i < len(s):
        c = s[i]
        if mode == 'n' and c in '~^':
            if buf:
                out.append(('n', buf))
                buf = ''
            mode = 'sub' if c == '~' else 'sup'
            i += 1
            continue
        if (mode == 'sub' and c == '~') or (mode == 'sup' and c == '^'):
            if buf:
                out.append((mode, buf))
                buf = ''
            mode = 'n'
            i += 1
            continue
        buf += c
        i += 1
    if buf:
        out.append((mode, buf))
    return out


def rich_segs(spec, size, bold=False):
    segs = []
    for kind, text in parse_rich(spec):
        if kind == 'n':
            segs.append((text, get_font(size, bold), 0))
        elif kind == 'sub':
            segs.append((text, get_font(size * 0.72, bold), int(round(size * 0.20 * SCALE))))
        else:
            segs.append((text, get_font(size * 0.72, bold), int(round(-size * 0.34 * SCALE))))
    return segs


def seg_width(segs):
    return sum(f.getlength(t) for t, f, _ in segs)


def draw_segs(dr, segs, x, y, color=C_BLACK, align=0.0):
    cx = x - seg_width(segs) * align
    for t, f, dy in segs:
        dr.text((cx, y + dy), t, font=f, fill=color, anchor='ls')
        cx += f.getlength(t)
    return cx


def draw_text(dr, x, y, s, size, color=C_BLACK, align=0.0, bold=False):
    return draw_segs(dr, rich_segs(s, size, bold), x, y, color, align)


def text_w(s, size, bold=False):
    return seg_width(rich_segs(s, size, bold)) / SCALE


def sci(v, nd=4):
    """返回 mini-markup 形式的科学计数法，如 7.0268×10^-19^"""
    if v == 0:
        return '0'
    e = int(math.floor(math.log10(abs(v))))
    man = v / (10.0 ** e)
    if abs(man) >= 10:
        man /= 10.0
        e += 1
    return ('{:.%df}' % nd).format(man) + '×10^' + str(e) + '^'


def dashed(dr, x0, y0, x1, y1, fill=C_GRID, width=1, dash=6, gap=5):
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    if L <= 0:
        return
    ux, uy = dx / L, dy / L
    t = 0.0
    while t < L:
        te = min(t + dash, L)
        dr.line([(x0 + ux * t, y0 + uy * t), (x0 + ux * te, y0 + uy * te)],
                fill=fill, width=width)
        t = te + gap


def marker(dr, x, y, kind, r, color=C_BLACK):
    ow = max(1, px(1.3))
    if kind == 'o':
        dr.ellipse([x - r, y - r, x + r, y + r], fill='white', outline=color, width=ow)
    elif kind == 'O':
        dr.ellipse([x - r, y - r, x + r, y + r], fill=color)
    elif kind == 's':
        dr.rectangle([x - r, y - r, x + r, y + r], fill='white', outline=color, width=ow)
    elif kind == '^':
        dr.polygon([(x, y - r * 1.2), (x - r * 1.15, y + r * 0.85), (x + r * 1.15, y + r * 0.85)],
                   fill='white', outline=color, width=ow)
    elif kind == 'v':
        dr.polygon([(x, y + r * 1.2), (x - r * 1.15, y - r * 0.85), (x + r * 1.15, y - r * 0.85)],
                   fill='white', outline=color, width=ow)
    elif kind == 'D':
        dr.polygon([(x, y - r * 1.25), (x + r * 1.25, y), (x, y + r * 1.25), (x - r * 1.25, y)],
                   fill='white', outline=color, width=ow)
    elif kind == 'd':
        dr.polygon([(x, y - r * 1.15), (x + r * 1.15, y), (x, y + r * 1.15), (x - r * 1.15, y)],
                   fill=color)
    elif kind == '+':
        dr.line([(x - r, y), (x + r, y)], fill=color, width=max(1, px(1.7)))
        dr.line([(x, y - r), (x, y + r)], fill=color, width=max(1, px(1.7)))
    elif kind == 'x':
        dr.line([(x - r, y - r), (x + r, y + r)], fill=color, width=max(1, px(1.7)))
        dr.line([(x - r, y + r), (x + r, y - r)], fill=color, width=max(1, px(1.7)))
    elif kind == 'h':
        dr.polygon([(x - r * 1.15, y), (x - r * 0.15, y - r), (x + r, y - r),
                    (x + r, y + r), (x - r * 0.15, y + r)],
                   fill='white', outline=color, width=ow)


class Axes(object):
    def __init__(self, dr, box, xlim, ylim):
        self.dr = dr
        self.l, self.t, self.r, self.b = [px(v) for v in box]
        self.xlim = xlim
        self.ylim = ylim

    def X(self, x):
        return self.l + (x - self.xlim[0]) / (self.xlim[1] - self.xlim[0]) * (self.r - self.l)

    def Y(self, y):
        return self.b - (y - self.ylim[0]) / (self.ylim[1] - self.ylim[0]) * (self.b - self.t)

    def frame(self):
        self.dr.rectangle([self.l, self.t, self.r, self.b], outline=C_BLACK, width=px(1.8))

    def grid(self, xticks, yticks):
        for xv in xticks:
            dashed(self.dr, self.X(xv), self.t, self.X(xv), self.b)
        for yv in yticks:
            dashed(self.dr, self.l, self.Y(yv), self.r, self.Y(yv))

    def ticks(self, xticks, yticks, xfmt='{:.0f}', yfmt='{:.0f}', size=17):
        for xv in xticks:
            x = self.X(xv)
            self.dr.line([(x, self.b), (x, self.b + px(7))], fill=C_BLACK, width=px(1.5))
            draw_text(self.dr, x, self.b + px(26), xfmt.format(xv), size, align=0.5)
        for yv in yticks:
            y = self.Y(yv)
            self.dr.line([(self.l - px(7), y), (self.l, y)], fill=C_BLACK, width=px(1.5))
            draw_text(self.dr, self.l - px(11), y + px(6), yfmt.format(yv), size, align=1.0)


def new_canvas():
    img = Image.new('RGB', (px(W), px(H)), 'white')
    return img, ImageDraw.Draw(img)


def save_fig(img, name):
    out = img.resize((W, H), Image.LANCZOS)
    path = os.path.join(FIGDIR, name)
    out.save(path)
    return path


def y_label(img, spec, size, cx, cy):
    segs = rich_segs(spec, size)
    w = int(seg_width(segs)) + px(10)
    h = int(size * 2.2 * SCALE)
    tmp = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    draw_segs(td, segs, px(5), int(h * 0.5 + size * 0.5 * SCALE), (0, 0, 0, 255))
    tmp = tmp.rotate(90, expand=True, resample=Image.BICUBIC)
    img.paste(tmp, (int(cx - tmp.width / 2), int(cy - tmp.height / 2)), tmp)


# ---------------------------------------------------------- 图 1: I_a - U_a
def fig_w1():
    img, dr = new_canvas()
    ax = Axes(dr, (150, 108, 1620, 1000), (0, 185), (0, 1250))
    xt = list(range(0, 181, 20))
    yt = list(range(0, 1201, 200))
    ax.grid(xt, yt)
    ax.frame()
    ax.ticks(xt, yt)
    draw_text(dr, (ax.l + ax.r) / 2, px(1052), '阳极电压  U~a~ / V', 21, align=0.5)
    y_label(img, '阳极电流  I~a~ / μA', 21, px(50), (ax.t + ax.b) / 2)
    draw_text(dr, W * SCALE / 2, px(56),
              '不同灯丝电流下的阳极电流 — 阳极电压曲线族', 27, align=0.5, bold=True)

    for i, row in enumerate(TAB1):
        col = PALETTE[i]
        pts = [(ax.X(u), ax.Y(v)) for u, v in zip(U_A, row)]
        dr.line(pts, fill=col, width=px(2.0), joint='curve')
        for (x, y) in pts:
            marker(dr, x, y, SHAPES[i], px(4.2), col)

    # 图例（左上方空白区 x<35, y>870）
    lx, ly = ax.X(6), ax.Y(1243)
    box_w, row_h = px(210), px(31)
    box_h = row_h * 8 + px(18)
    dr.rectangle([lx, ly, lx + box_w, ly + box_h], fill='white',
                 outline=(125, 125, 125), width=px(1.2))
    for i, ifv in enumerate(I_F):
        cy = ly + px(13) + row_h * i + row_h // 2
        col = PALETTE[i]
        dr.line([(lx + px(12), cy), (lx + px(46), cy)], fill=col, width=px(2.0))
        marker(dr, lx + px(29), cy, SHAPES[i], px(4.2), col)
        draw_text(dr, lx + px(56), cy + px(7), 'I~f~ = {:.3f} A'.format(ifv), 16, color=col)

    # 注释：箭头 + 两行文字（x 120~170, y 780~1040 为空区）
    ax0 = ax.X(130)
    dr.line([(ax0, ax.Y(790)), (ax0, ax.Y(1022))], fill=C_BLACK, width=px(1.6))
    dr.polygon([(ax0, ax.Y(1048)), (ax0 - px(6), ax.Y(1020)), (ax0 + px(6), ax.Y(1020))],
               fill=C_BLACK)
    draw_text(dr, ax.X(142), ax.Y(1020), '灯丝电流 I~f~ 越大', 19)
    draw_text(dr, ax.X(142), ax.Y(958), '曲线整体上移', 19)
    return save_fig(img, 'fig_w1.png')


# ------------------------------------------------- 图 2: lg I_a - sqrt(U_a)
def fig_w2():
    img, dr = new_canvas()
    ax = Axes(dr, (150, 108, 1620, 1000), (0, 14), (0.80, 3.30))
    xt = list(range(0, 13, 2))
    yt = [1.0 + 0.2 * i for i in range(12)]
    ax.grid(xt, yt)
    ax.frame()
    ax.ticks(xt, yt, yfmt='{:.1f}')
    draw_text(dr, (ax.l + ax.r) / 2, px(1052),
              '√U~a~ / V^1/2^', 21, align=0.5)
    y_label(img, 'lg I~a~', 21, px(50), (ax.t + ax.b) / 2)
    draw_text(dr, W * SCALE / 2, px(56),
              '各温度下 lg I~a~ — √U~a~ 拟合直线族（外延到 √U~a~ = 0 求 lg I~s~）',
              27, align=0.5, bold=True)

    rows = TAB2 + [TAB2_ROW_216]
    temps = T2 + [T216]
    for i, (t, row) in enumerate(zip(temps, rows)):
        col = PALETTE[i]
        f = linfit(SQRU, row)
        m, b = f['slope'], f['intercept']
        dr.line([(ax.X(0.0), ax.Y(b)), (ax.X(12.0), ax.Y(m * 12.0 + b))],
                fill=col, width=px(1.6))
        for (u, v) in zip(SQRU, row):
            marker(dr, ax.X(u), ax.Y(v), SHAPES[i], px(3.8), col)
        marker(dr, ax.X(0.0), ax.Y(b), 'd', px(5.5), col)
        draw_text(dr, ax.X(12.34), ax.Y(m * 12.0 + b) + px(6.5),
                  '{:.2f}'.format(t), 17, color=col)

    draw_text(dr, ax.X(13.90), ax.Y(3.245), 'T/10^3^K', 16, align=1.0)

    # 底部说明：位于 y < 1.0 的整幅空白带，不压任何直线，无需白底
    note1 = ('◆ 外推截距 lg I~s~ = '
             + ' / '.join('{:.2f}'.format(b) for b in LG_IS_ALL)
             + '（按 T 由 1.88 到 2.16 排列）')
    note2 = ('◆ 横轴 √U~a~（V^1/2^）取 5 到 12；右端彩色数字为各直线对应的 T/10^3^K；'
             '所有直线均已外延到 √U~a~ = 0')
    draw_text(dr, ax.X(0.35), ax.Y(1.038), note1, 17)
    draw_text(dr, ax.X(0.35), ax.Y(0.925), note2, 15)
    return save_fig(img, 'fig_w2.png')


# --------------------------------------------- 图 3: lg(I_s/T^2) - 1/T
def fig_w3():
    img, dr = new_canvas()
    ax = Axes(dr, (150, 108, 1620, 1000), (0.445, 0.545), (0.55, 3.55))
    xt = [round(0.45 + 0.01 * i, 3) for i in range(10)]
    yt = [round(0.6 + 0.2 * i, 3) for i in range(15)]
    ax.grid(xt, yt)
    ax.frame()
    ax.ticks(xt, yt, xfmt='{:.2f}', yfmt='{:.1f}')
    draw_text(dr, (ax.l + ax.r) / 2, px(1052), '1/T  /  10^-3^ K^-1^', 21, align=0.5)
    y_label(img, 'lg ( I~s~ / T^2^ )', 21, px(50), (ax.t + ax.b) / 2)
    draw_text(dr, W * SCALE / 2, px(56),
              'lg ( I~s~ / T^2^ ) — 1/T 直线（理查森—杜什曼关系）', 27,
              align=0.5, bold=True)

    m, b = FIT_T3['slope'], FIT_T3['intercept']
    y_at = lambda x: m * x + b
    xin = max((ax.ylim[1] - b) / m, ax.xlim[0])
    xout = min((ax.ylim[0] - b) / m, ax.xlim[1])
    dr.line([(ax.X(xin), ax.Y(y_at(xin))), (ax.X(xout), ax.Y(y_at(xout)))],
            fill=PALETTE[2], width=px(2.2))
    for (x, y) in zip(T3_INV, T3_LGR):
        marker(dr, ax.X(x), ax.Y(y), 'O', px(5.4), PALETTE[1])
    for (x, y, t) in zip(T3_INV, T3_LGR, T3):
        draw_text(dr, ax.X(x) + px(12), ax.Y(y) - px(9), '{:.2f}'.format(t),
                  14, color=PALETTE[1])

    # 参数框（坐标框内上方空白区）
    lines = [
        ('直线斜率  m = {:.3f}     （横轴单位 10^-3^ K^-1^）'.format(m), 19),
        ('换算斜率  m′ = m × 10^3^ = {} K^-1^'.format(sci(M_TRUE, 4)), 19),
        ('截距  b = {:.3f}      r = {:.5f}      r^2^ = {:.5f}'.format(
            b, FIT_T3['r'], FIT_T3['r2']), 19),
        ('逸出功  eφ = 2.303 k |m′| = {:.3f} eV'.format(PHI_EV), 19),
        ('          = {} J'.format(sci(PHI_J, 4)), 19),
        ('相对误差  E = {:+.2f} %    （公认值 eφ = 4.54 eV）'.format(REL_ERR), 19),
    ]
    lines = [(s.replace('-', '\u2212'), sz) for s, sz in lines]
    bw = max(text_w(s, sz) for s, sz in lines) + 46
    bh = 30 * len(lines) + 46
    bx = ax.X(0.4475)
    by = ax.Y(3.50)
    dr.rectangle([bx, by, bx + px(bw), by + px(bh)], fill='white')
    dr.rectangle([bx, by, bx + px(bw), by + px(32)], fill=(236, 236, 236))
    dr.rectangle([bx, by, bx + px(bw), by + px(bh)], outline=(80, 80, 80), width=px(1.4))
    dr.line([(bx, by + px(32)), (bx + px(bw), by + px(32))], fill=(80, 80, 80), width=px(1.4))
    draw_text(dr, bx + px(bw) / 2, by + px(23), '最 小 二 乘 拟 合 结 果', 18, align=0.5, bold=True)
    for i, (s, sz) in enumerate(lines):
        draw_text(dr, bx + px(20), by + px(52 + 30 * i), s, sz)

    # 右上角图例：先量出最长文字宽度，再在其左侧留出样例线/样例点
    leg_items = [('最小二乘直线', 16), ('实测点（括号内为 T/10^3^K）', 15)]
    tw = max(text_w(s, sz) for s, sz in leg_items)
    lx = ax.X(0.5445)
    ly = ax.Y(3.335)
    sx = lx - px(tw) - px(34)
    dr.line([(sx, ly), (sx + px(26), ly)], fill=PALETTE[2], width=px(2.2))
    draw_text(dr, lx, ly + px(6), leg_items[0][0], leg_items[0][1], align=1.0)
    marker(dr, sx + px(13), ly - px(33), 'O', px(5.4), PALETTE[1])
    draw_text(dr, lx, ly - px(27), leg_items[1][0], leg_items[1][1], align=1.0)
    return save_fig(img, 'fig_w3.png')


# ------------------------------------------------------------ read_report ---
def fmt_grid(header, rows):
    w = [max(len(str(h)), *(len(str(r[i])) for r in rows)) for i, h in enumerate(header)]
    out = ['  '.join(str(h).rjust(w[i]) for i, h in enumerate(header))]
    out.append('  '.join('-' * w[i] for i in range(len(header))))
    for r in rows:
        out.append('  '.join(str(v).rjust(w[i]) for i, v in enumerate(r)))
    return out


def wrap_cn(s, width):
    """按 width 折行：优先在中文标点后断；绝不切断连续的 ASCII 词/数字串。"""
    out = []
    s = s.strip()
    while len(s) > width:
        cut = -1
        for i in range(width, max(width - 18, 8) - 1, -1):
            if s[i - 1] in '，。；、：）, ':
                cut = i
                break
        if cut < 0:
            cut = width
            while (cut > 8 and s[cut - 1].isascii() and not s[cut - 1].isspace()
                   and s[cut].isascii() and not s[cut].isspace()):
                cut -= 1
        out.append(s[:cut].rstrip())
        s = s[cut:].lstrip()
    if s:
        out.append(s)
    return out


def build_report():
    L = []
    A = L.append
    A('=' * 78)
    A('钨的逸出功测定 —— 原始读数判读记录与计算结果')
    A('素材：04_生成过程_脚本图表\\src_new.png (3072x4096，学生手写原始数据页)')
    A('=' * 78)
    A('')
    A('【零】判读方法')
    A('  把 3072x4096 原图按 1200~1600 px 宽 x 600~900 px 高分块裁切（必要时再放大 1.4~4 倍），')
    A('  逐块 read_image，逐格抄录；再用两条独立校验交叉验证读数：')
    A('  (a) 表 1 逐格取 lg，与表 2 逐格比对（残差见 §4）；')
    A('  (b) 表 3 第 3 行 / 第 4 行应满足  第4行 = 第3行 - 2lg(T/10^3)（见 §6）。')
    A('')
    A('【一】表 1：不同灯丝电流 I_f 和阳极电压 U_a 对应的阳极电流 I_a（单位 μA）')
    hdr = ['I_f/A'] + ['U_a=%d' % u for u in U_A]
    L.extend(fmt_grid(hdr, [['%.3f' % ifv] + ['%d' % v for v in row]
                            for ifv, row in zip(I_F, TAB1)]))
    A('')
    A('【二】表 2：不同温度 T 和 √U_a 下对应的阳极电流的对数值 lg I_a')
    A('  印刷网格内只有 7 行（1.88 ~ 2.12）：')
    hdr = ['T/10^3K'] + ['√U_a=%d' % s for s in SQRU]
    L.extend(fmt_grid(hdr, [['%.2f' % t] + ['%.2f' % v for v in row]
                            for t, row in zip(T2, TAB2)]))
    A('')
    A('  网格底线之外、表 3 标题之上另有一行手写数字（未写行标签）：')
    A('    ' + '  '.join('%.2f' % v for v in TAB2_ROW_216))
    A('')
    A('【三】表 2 底部那行的判读结论')
    A('  结论：它是 T = 2.16×10^3 K 这一行的 lg I_a，不是外推截距 lg I_s。')
    A('  依据 1（数值对撞，决定性）：表 1 第 8 行 I_f=0.775 A 的 I_a =')
    A('          1030 1050 1071 1081 1112 1129 1144 1162 μA，取 lg 得')
    A('          ' + '  '.join('%.4f' % v for v in ROW216_LG))
    A('          手写行 = ' + '  '.join('%.2f' % v for v in TAB2_ROW_216))
    A('          8 格全部吻合（最大偏差 %.4f），即两位有效数字完全对上。' % CHECK_216['max_abs_diff_lg'])
    A('  依据 2（温度序列）：8 个灯丝电流按 T = 920.0 + 1600·I_f 正好给出')
    A('          1.88/1.92/1.96/2.00/2.04/2.08/2.12/2.16 ×10^3 K，表 2 缺的正是第 8 行；')
    A('          该行数字落在表 2 底线正下方，位置、量级、单调递增趋势都与“第 8 行数据”一致。')
    A('  依据 3（反证）：若它是外推截距，数量级应落在拟合截距区间 [1.30, 2.97] 内；')
    A('          而这一行是 3.01~3.07，与表 2 各行 lg I_a 高端同量级，且缺少任何外推记号。')
    A('  处理：表 2 按 8 行数据使用（第 8 行记作 T=2.16×10^3 K），图 2 画 8 条直线；')
    A('        T=2.16 行的拟合结果也单列在 §7 中。')
    A('')
    A('【四】表 1 逐格 lg 与表 2 逐格比对的残差（读数自检）')
    for c in CHECK_T12:
        A('  T=%.2f×10^3K : 最大偏差 %.3f ，平均偏差 %.3f' %
          (c['T_1000K'], c['max_abs_diff_lg'], c['mean_abs_diff_lg']))
    A('  T=2.16×10^3K : 最大偏差 %.4f（表 2 补写行 vs 表 1 第 8 行的 lg）'
      % CHECK_216['max_abs_diff_lg'])
    A('  → 表 1 与表 2 是同一批数据，读数自洽，差异只来自学生的四舍五入。')
    A('')
    A('【五】表 3：lg(I_s/T²) ~ 1/T 数据表')
    for r in ([['T/10^3K'] + ['%.2f' % v for v in T3],
               ['1/T(10^-3K^-1)'] + ['%.2f' % v for v in T3_INV],
               ['lgI'] + ['%.2f' % v for v in T3_LGI],
               ['lg(I_s/T^2)'] + ['%.2f' % v for v in T3_LGR]]):
        A('  ' + '  '.join('%12s' % c for c in r))
    A('')
    A('  第 4 行行标题：印刷体为 “lgI（I/T²）”，括号内分子是大写 I（与 “lgI” 里的 I 同字形），')
    A('  不是数字 1；配合本表标题 “表 3  lg（I_s/T²）~1/T 数据表” 与下面的数值关系，')
    A('  判定该行为 lg(I_s/T²)。')
    A('')
    A('  待填空白：「逸出功公认值 eφ = 4.54eV」「直线斜率 m =」「逸出功 eφ =」「相对误差 E =」')
    A('  四个空均无手写答案，属未完成项，需在报告中补齐（本文 §8~§9 给出）。')
    A('')
    A('【六】常数偏移 6 的核对 —— 确认不影响斜率')
    A('  学生算 lg(T²) 时把 T 代成了 T/10^3 K：')
    A('    lg(T²)|用 T/10^3  = 2lg(T/10^3) = (2lgT) - 6 = lg(T²)|真实 - 6')
    A('  故  第4行 = lgI - 2lg(T/10^3) = lg(I_s/T²)|真实 + 6 。')
    A('  逐点核对 第3行 - 第4行 (实测) = ' + '  '.join('%.2f' % v for v in OFFSET_CHECK))
    A('           2lg(T/10^3)   (计算) = ' + '  '.join('%.3f' % v for v in LG_T_1E3))
    A('  → 两行逐点相符，最大偏差 %.3f（学生只保留两位小数所致）；平均值 %.4f。'
      % (max(abs(a - b) for a, b in zip(OFFSET_CHECK, LG_T_1E3)), OFFSET_MEAN))
    A('  2lgT      = ' + '  '.join('%.3f' % v for v in LG_T_TRUE))
    A('  2lg(T/1e3)= ' + '  '.join('%.3f' % v for v in LG_T_1E3))
    A('  2lgT - 2lg(T/1e3) 恒等于 2lg(1000) = 6.000（8 点全部成立）。')
    A('  也就是说：第 4 行比真实的 lg(I_s/T²) 处处高 6.000，等价于学生把 lg(T²) 写成了')
    A('  lg((T/10^3)²)，漏掉了 10^3 的平方因子；这是一个只平移、不改变形状的常数偏移。')
    A('  最小二乘斜率 = Σ(x-x̄)(y-ȳ)/Σ(x-x̄)²，y 整体平移常数时')
    A('  ȳ 同步平移、y-ȳ 不变，因此斜率完全不变：')
    A('    用原始第 4 行    拟合斜率 = %.6f' % FIT_T3['slope'])
    A('    用第 4 行 - 6.0  拟合斜率 = %.6f' % FIT_OFFSET6['slope'])
    A('    两者之差 = %.2e  → 平移 6 不影响 eφ，只让截距 b 差 6.0。'
      % abs(FIT_OFFSET6['slope'] - FIT_T3['slope']))
    A('')
    A('【七】加速电场外延法：表 2 逐温度最小二乘直线（x = √U_a，y = lg I_a）')
    A('  T/10^3K     斜率        截距 lg I_s       r          r^2')
    for f in FITS_T2:
        A('  %5.2f   %+10.5f   %9.4f   %9.6f   %9.6f' %
          (f['T_1000K'], f['slope'], f['intercept'], f['r'], f['r2']))
    A('  %5.2f   %+10.5f   %9.4f   %9.6f   %9.6f   <- 补写的第 8 行' %
      (T216, FIT_T216['slope'], FIT_T216['intercept'], FIT_T216['r'], FIT_T216['r2']))
    A('')
    A('  8 个温度外推截距 lg I_s = ' + ' / '.join('%.3f' % v for v in LG_IS_ALL))
    A('  表 3 第 3 行学生自填值 = ' + ' / '.join('%.2f' % v for v in T3_LGI))
    A('  最大差 %.3f —— 学生第 3 行确实是“外延法截距”，读数无误。' %
      max(abs(a - b) for a, b in zip(LG_IS_ALL, T3_LGI)))
    A('')
    A('【八】主拟合：表 3 原始数据（x = 1/T 以 10^-3 K^-1 计，y = 第 4 行）')
    A('  n            = %d' % FIT_T3['n'])
    A('  斜率 m       = %.6f' % FIT_T3['slope'])
    A('  斜率标准差   = %.6f' % FIT_T3['se_slope'])
    A('  截距 b       = %.6f' % FIT_T3['intercept'])
    A('  截距标准差   = %.6f' % FIT_T3['se_intercept'])
    A('  r            = %.8f' % FIT_T3['r'])
    A('  r^2          = %.8f' % FIT_T3['r2'])
    A('  残差标准差 s = %.6f' % FIT_T3['s_resid'])
    A('  拟合式：y = %.4f · x + %.4f' % (FIT_T3['slope'], FIT_T3['intercept']))
    A('')
    A('【九】逸出功')
    A('  m_true = m × 10^3 = %.4f  K^-1' % M_TRUE)
    A('  eφ = 2.303 · k · |m_true| ，k = 1.3806505e-23 J/K ，e = 1.602e-19 C')
    A('     = 2.303 × 1.3806505e-23 × %.4f' % abs(M_TRUE))
    A('     = %.6e J' % PHI_J)
    A('     = %.6e J / %.6e C = %.4f eV' % (PHI_J, E_CHARGE, PHI_EV))
    A('  公认值 eφ = 4.54 eV')
    A('  绝对误差 = %+.4f eV' % ABS_ERR)
    A('  相对误差 E = (%.4f - 4.54) / 4.54 = %+.3f %%' % (PHI_EV, REL_ERR))
    A('')
    A('【十】稳健性变体')
    A('  A. 横坐标改用未截断的 1/(T·10^3)：斜率 = %.4f，b = %.4f，r^2 = %.6f'
      % (FIT_T3_EXACT['slope'], FIT_T3_EXACT['intercept'], FIT_T3_EXACT['r2']))
    A('     -> eφ = %.4f eV' % PHI_EV_EXACT)
    A('  B. 纵坐标改用本次由表 2 外推的 lg I_s 重算（lg(I_s/T^2) 真实值）：')
    A('     斜率 = %.4f，b = %.4f，r^2 = %.6f'
      % (FIT_T3_RECOMP['slope'], FIT_T3_RECOMP['intercept'], FIT_T3_RECOMP['r2']))
    A('     -> eφ = %.4f eV' % PHI_EV_RECOMP)
    _rels = [(v - PHI_ACCEPT_EV) / PHI_ACCEPT_EV * 100.0
             for v in (PHI_EV, PHI_EV_EXACT, PHI_EV_RECOMP)]
    A('  结论：三种做法的 eφ 依次为 %.4f / %.4f / %.4f eV，'
      % (PHI_EV, PHI_EV_EXACT, PHI_EV_RECOMP))
    A('        相对误差依次为 %+.2f%% / %+.2f%% / %+.2f%%，全部落在 %.1f%% ~ %.1f%%，'
      % (_rels[0], _rels[1], _rels[2], min(_rels), max(_rels)))
    A('        即横坐标若坚持用学生截断的 0.53/0.52/… ，偏差最大（约 %.1f%%）；'
      % abs(_rels[0]))
    A('        判读取整带来的差异不足以改变“eφ 略低于公认值 4.54 eV”这一结论。')
    A('')
    A('【十一】判读存疑清单（最终取值见前表）')
    for i, (c, n) in enumerate(AMBIGUOUS, 1):
        A('  %d) %s' % (i, c))
        for ln in wrap_cn(n, 72):
            A('     ' + ln)
    A('')
    A('【十二】产出')
    A('  build_data_tungsten.py        —— 本脚本（幂等）')
    A('  data_tungsten.json            —— 三张原始表 + 中间量 + 全部拟合结果')
    A('  figures_tungsten\\fig_w1.png   —— I_a-U_a 曲线族（8 条）')
    A('  figures_tungsten\\fig_w2.png   —— lg I_a-√U_a 直线族（8 条，外延到 √U_a=0）')
    A('  figures_tungsten\\fig_w3.png   —— lg(I_s/T²)-1/T 直线 + 参数框')
    A('  read_report.txt               —— 本文件')
    return '\n'.join(L) + '\n'


# ------------------------------------------------------------------- main ---
if __name__ == '__main__':
    p1 = fig_w1()
    p2 = fig_w2()
    p3 = fig_w3()
    with open(REPORT_PATH, 'w', encoding='utf-8') as fh:
        fh.write(build_report())
    msg = ['JSON  : %s' % JSON_PATH, 'REPORT: %s' % REPORT_PATH]
    for p in (p1, p2, p3):
        im = Image.open(p)
        msg.append('FIG   : %s  %dx%d' % (p, im.width, im.height))
    msg.append('m_plot=%.6f  b=%.6f  r2=%.8f  phi=%.4f eV  rel=%.3f%%'
               % (M_PLOT, FIT_T3['intercept'], FIT_T3['r2'], PHI_EV, REL_ERR))
    with open(os.path.join(BASE, 'build_tungsten_log.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(msg) + '\n')
