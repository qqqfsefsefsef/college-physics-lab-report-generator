# -*- coding: utf-8 -*-
"""
光电效应的研究 —— 数据处理 + 三张 Pillow 手绘图（无 matplotlib，幂等可重复运行）

输出：
  data.json
  figures/fig_va.png     光电管的伏安特性曲线
  figures/fig_u0nu.png   截止电压与入射光频率的关系
  figures/fig_ip.png     饱和电流与光阑孔面积的关系

运行：python build_data.py（只覆盖上述文件，不动目录中其它文件）
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FIGDIR = ROOT / "figures"
FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"   # 微软雅黑：中文 + 希腊字母 + 数学符号齐全

E_CHARGE = 1.602e-19      # 元电荷 (C)
H0 = 6.626e-34            # 普朗克常量公认值 (J·s)

# --------------------------------------------------------------------------
# 1. 原始数据（已由手写记录页核对，直接使用）
# --------------------------------------------------------------------------
TABLE1 = [
    {
        "lambda_nm": 435.8,
        "phi_mm": 2,
        "U_AK_V": [-4, -3, -2, -1, 0, 1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30],
        "I": [0.9, 1.3, 1.7, 2.2, 2.9, 9.0, 13.6, 16.9, 19.4, 22.6, 27.0, 30.3, 33.0,
              35.3, 37.0, 39.0, 40.7, 42.3, 43.7, 45.0, 45.9, 46.8],
    },
    {
        "lambda_nm": 546.1,
        "phi_mm": 4,
        "U_AK_V": [-4, -3, -2, -1, 0, 1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30],
        "I": [0.5, 0.1, 0.4, 2.0, 3.3, 13.5, 19.3, 24.9, 30.3, 35.3, 40.8, 45.2, 48.6,
              51.4, 53.8, 56.1, 58.2, 60.0, 61.7, 63.1, 64.4, 66.2],
    },
]

TABLE2 = {
    "U_AK_V": 30,
    "series": [
        {"lambda_nm": 435.8, "phi_mm": [2, 4, 8], "I_M": [46.8, 173.0, 687.0]},
        {"lambda_nm": 546.1, "phi_mm": [2, 4, 8], "I_M": [18.0, 65.6, 256.8]},
    ],
}

TABLE3 = {
    "lambda_nm": [365.0, 404.7, 435.8, 546.1, 577.0],
    "nu_1014Hz": [8.216, 7.410, 6.882, 5.492, 5.196],
    "U0_runs": [
        [-1.490, -0.917, -0.627, -0.192, -0.169],
        [-1.507, -0.920, -0.640, -0.200, -0.180],
        [-1.515, -0.927, -0.656, -0.209, -0.176],
    ],
}


# --------------------------------------------------------------------------
# 2. 计算
# --------------------------------------------------------------------------
def round_sig(value: float, digits: int = 6) -> float:
    """保留有效数字（返回 float，便于 JSON 直接序列化）。"""
    if value == 0 or not math.isfinite(value):
        return value
    return float(f"{value:.{digits}g}")


def linfit_with_intercept(x, y):
    """最小二乘 y = a*x + b，返回 slope/intercept/r/r2/residuals。"""
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    sxx = sum((xi - mx) ** 2 for xi in x)
    syy = sum((yi - my) ** 2 for yi in y)
    sxy = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    a = sxy / sxx
    b = my - a * mx
    r = sxy / math.sqrt(sxx * syy)
    resid = [yi - (a * xi + b) for xi, yi in zip(x, y)]
    return {"slope": a, "intercept": b, "r": r, "r2": r * r,
            "residuals": resid, "sxx": sxx, "syy": syy, "sxy": sxy}


def linfit_through_origin(x, y):
    """过原点最小二乘 y = a*x，返回 slope/r2(相对 y 均值)/residuals。"""
    sxy = sum(xi * yi for xi, yi in zip(x, y))
    sxx = sum(xi * xi for xi in x)
    a = sxy / sxx
    n = len(y)
    my = sum(y) / n
    syy = sum((yi - my) ** 2 for yi in y)
    ss_res = sum((yi - a * xi) ** 2 for xi, yi in zip(x, y))
    resid = [yi - a * xi for xi, yi in zip(x, y)]
    return {"slope": a, "intercept": 0.0, "r2": 1.0 - ss_res / syy,
            "residuals": resid}


def build_data():
    # ---- 表3：U0 平均值（负值） ----
    u0_avg = []
    u0_std = []
    for j in range(len(TABLE3["lambda_nm"])):
        col = [run[j] for run in TABLE3["U0_runs"]]
        m = sum(col) / len(col)
        u0_avg.append(round(m, 4))
        u0_std.append(round(math.sqrt(sum((c - m) ** 2 for c in col) / (len(col) - 1)), 4))

    nu14 = TABLE3["nu_1014Hz"]
    nu_hz = [v * 1e14 for v in nu14]
    u_s = [abs(v) for v in u0_avg]          # U_s = |U0|

    # ---- 两种直线拟合：U_s = K*nu + b ----
    fit_abs = linfit_with_intercept(nu14, u_s)          # x 用 10^14 Hz 单位
    a14 = fit_abs["slope"]                              # V / (10^14 Hz)
    K = a14 / 1e14                                      # V·s
    b = fit_abs["intercept"]                            # V
    h_fit = E_CHARGE * K
    rel_err = abs(h_fit - H0) / H0 * 100.0

    fit_origin = linfit_through_origin(nu14, u_s)
    a0 = fit_origin["slope"]
    K0 = a0 / 1e14
    h0_fit = E_CHARGE * K0
    rel_err0 = abs(h0_fit - H0) / H0 * 100.0
    # 过原点模型的 Pearson r（与带截距相同，仅供对照，另给 R2_origin）
    r_pearson = fit_abs["r"]

    fit_block = {
        "with_intercept": {
            "form": "U_s = K*nu + b   (nu 以 10^14 Hz 为单位时斜率为 a14)",
            "slope_a14_V_per_1e14Hz": round_sig(a14, 6),
            "slope_K_Vs": round_sig(K, 6),
            "intercept_b_V": round_sig(b, 6),
            "r": round_sig(fit_abs["r"], 6),
            "r2": round_sig(fit_abs["r2"], 6),
            "h_Js": round_sig(h_fit, 6),
            "h_1e34": round_sig(h_fit * 1e34, 6),
            "rel_err_pct": round_sig(rel_err, 4),
            "work_function_eV": round_sig(-b, 6),   # W = -b*e  →  eV
            "residuals_V": [round_sig(v, 4) for v in fit_abs["residuals"]],
            "max_abs_residual_V": round_sig(max(abs(v) for v in fit_abs["residuals"]), 4),
        },
        "through_origin": {
            "form": "U_s = K0*nu   (强制过原点)",
            "slope_a14_V_per_1e14Hz": round_sig(a0, 6),
            "slope_K_Vs": round_sig(K0, 6),
            "intercept_b_V": 0.0,
            "r": round_sig(r_pearson, 6),
            "r2": round_sig(fit_origin["r2"], 6),
            "h_Js": round_sig(h0_fit, 6),
            "h_1e34": round_sig(h0_fit * 1e34, 6),
            "rel_err_pct": round_sig(rel_err0, 4),
            "residuals_V": [round_sig(v, 4) for v in fit_origin["residuals"]],
        },
        "primary": "with_intercept",
    }

    # ---- 各波长单点 h_i = e*|U0_i| / nu_i ----
    per_point = []
    for lam, n14, n_hz, u in zip(TABLE3["lambda_nm"], nu14, nu_hz, u_s):
        hi = E_CHARGE * u / n_hz
        per_point.append({
            "lambda_nm": lam,
            "nu_1014Hz": n14,
            "U_s_V": round(u, 6),
            "h_i_Js": round_sig(hi, 6),
            "h_i_1e34": round_sig(hi * 1e34, 6),
            "rel_err_pct": round_sig(abs(hi - H0) / H0 * 100.0, 4),
        })

    # ---- 表2：I_M ∝ Phi^2 检验 ----
    t2_check = {"series": [], "U_AK_V": TABLE2["U_AK_V"],
                "theory_ratio": [1.0, 4.0, 16.0]}
    for s in TABLE2["series"]:
        phis = s["phi_mm"]
        ims = s["I_M"]
        phi2 = [p * p for p in phis]
        im_over_phi2 = [im / (p * p) for im, p in zip(ims, phis)]
        base = ims[0]
        # 归一化：以 Φ=2 mm 的 I_M 为 1，理论上应为 1 : 4 : 16
        norm = [v / base for v in ims]
        dev = [(v - t) / t * 100.0 for v, t in zip(norm, t2_check["theory_ratio"])]
        # 过原点线性拟合 I_M = c*Phi^2
        c = sum(a * b_ for a, b_ in zip(phi2, ims)) / sum(a * a for a in phi2)
        my = sum(ims) / len(ims)
        ss_res = sum((im - c * p2) ** 2 for im, p2 in zip(ims, phi2))
        ss_tot = sum((im - my) ** 2 for im in ims)
        t2_check["series"].append({
            "lambda_nm": s["lambda_nm"],
            "phi_mm": phis,
            "phi2_mm2": phi2,
            "I_M": ims,
            "I_M_over_phi2": [round_sig(v, 6) for v in im_over_phi2],
            "normalized_I_M": [round_sig(v, 6) for v in norm],
            "theory_normalized": t2_check["theory_ratio"],
            "deviation_pct": [round_sig(v, 4) for v in dev],
            "max_abs_deviation_pct": round_sig(max(abs(v) for v in dev), 4),
            "fit_through_origin_c_per_mm2": round_sig(c, 6),
            "r2_through_origin": round_sig(1.0 - ss_res / ss_tot, 6),
        })
    t2_check["conclusion"] = (
        "两波长下 I_M/Φ² 近似为常数，归一化比约为 1 : 3.7 : 14.7（理论 1 : 4 : 16），"
        "最大相对偏差约 11%，饱和电流与光强（∝Φ²）在实验精度内成正比，"
        "偏差随 Φ 增大而略偏小，可归因于大孔径时边缘场不均匀与光斑未全部覆盖阴极。"
    )

    # ---- 表1：饱和电流与曲线形状 ----
    t1_analysis = {"series": []}
    for s in TABLE1:
        u = s["U_AK_V"]
        i = s["I"]
        d = dict(zip(u, i))
        i30 = d[30]
        i20 = d[20]
        i0 = d[0]
        i4 = d[4]
        i10 = d[10]
        rel_20_30 = (i30 - i20) / i20 * 100.0
        rise_ratio = (i30 - i0) / i0
        frac_by_10 = (i10 - i0) / (i30 - i0) * 100.0
        mono = all(i[k + 1] > i[k] for k in range(len(i) - 1))
        t1_analysis["series"].append({
            "lambda_nm": s["lambda_nm"],
            "phi_mm": s["phi_mm"],
            "I_at_30V": i30,
            "I_at_20V": i20,
            "I_at_0V": i0,
            "I_at_4V": i4,
            "saturation_rel_change_20_30V_pct": round_sig(rel_20_30, 4),
            "rise_factor_0V_to_30V": round_sig(rise_ratio, 4),
            "rise_completed_by_10V_pct": round_sig(frac_by_10, 4),
            "monotonic_increasing": mono,
            "rise_edge_span_V": "0 V ~ +4 V（I 由约 3 增至 19~30）",
        })
    f435 = t1_analysis["series"][0]
    f546 = t1_analysis["series"][1]
    t1_analysis["conclusion"] = (
        "两条曲线均为先陡升后饱和：U_AK 由 0 V 增至 4 V 时 I 迅速上升，"
        f"10 V 时已分别完成全程增量的 {f435['rise_completed_by_10V_pct']:.0f}% 与 "
        f"{f546['rise_completed_by_10V_pct']:.0f}%，"
        f"20~30 V 区间 I 仅再增加 {f435['saturation_rel_change_20_30V_pct']:.1f}% 与 "
        f"{f546['saturation_rel_change_20_30V_pct']:.1f}%，即进入饱和区，符合光电效应的伏安特性。"
    )

    # ---- 暗电流 / 反向电流 ----
    dark = {
        "source": "表1 中 U_AK = -4 V 处（即为该波长、该光阑下的反向/暗电流水平）",
        "435.8nm_2mm_I_at_-4V": 0.9,
        "546.1nm_4mm_I_at_-4V": 0.5,
        "365.0nm_curve_available": False,
        "note": "365.0 nm 一组只测了截止电压（表3），没有伏安曲线，故其暗电流未测；"
                "此处以 435.8 nm、Φ=2 mm 曲线的 -4 V 读数 0.9×10^-11 A 作为暗电流量级参考，"
                "约为饱和电流 46.8×10^-11 A 的 1.9%。",
    }

    data = {
        "meta": {
            "project": "光电效应的研究 —— 实验报告数据表",
            "original_data_unit": {"I": "10^-11 A", "U_AK": "V", "U0": "V（记录为负值）"},
            "constants": {"e_C": E_CHARGE, "h0_Js": H0,
                          "note": "h_i 单点值 = e·|U0_i|/ν_i 未扣除逸出功，系统性偏低，仅作讨论用"},
            "source_script": "build_data.py（幂等，可直接重跑）",
        },
        "tables": {
            "table1": TABLE1,
            "table2": TABLE2,
            "table3": {
                "lambda_nm": TABLE3["lambda_nm"],
                "nu_1014Hz": TABLE3["nu_1014Hz"],
                "U0_runs": TABLE3["U0_runs"],
                "U0_avg_V": u0_avg,
                "U0_std_V": u0_std,
            },
        },
        "u0_avg": {
            "lambda_nm": TABLE3["lambda_nm"],
            "nu_1014Hz": nu14,
            "nu_Hz": [round_sig(v, 8) for v in nu_hz],
            "U0_avg_V": u0_avg,
            "U0_std_V": u0_std,
            "U_s_V": [round_sig(v, 6) for v in u_s],
        },
        "fit": fit_block,
        "per_point_h": per_point,
        "table2_check": t2_check,
        "table1_analysis": t1_analysis,
        "dark_current": dark,
        "figures": {
            "va": "figures/fig_va.png",
            "u0nu": "figures/fig_u0nu.png",
            "ip": "figures/fig_ip.png",
        },
    }
    return data


# --------------------------------------------------------------------------
# 3. Pillow 绘图基础工具（2 倍超采样 + LANCZOS 缩放）
# --------------------------------------------------------------------------
S = 2                     # 超采样倍数
W_FINAL = 1725            # 成品宽度 px（14.6 cm @300 dpi）
BLACK = (0, 0, 0)
GRAY = (140, 140, 140)
LIGHT = (205, 205, 205)
BLUE = (26, 62, 148)      # 435.8 nm
RED = (150, 28, 38)       # 546.1 nm
GREEN = (0, 110, 70)      # 拟合线

_font_cache = {}


def F(size_final: float) -> ImageFont.FreeTypeFont:
    """按成品字号取字体（自动乘超采样倍数）。"""
    key = size_final
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(FONT_PATH, max(6, int(round(size_final * S))))
    return _font_cache[key]


SUP_SCALE, SUP_RISE = 0.62, 0.42
SUB_SCALE, SUB_DROP = 0.62, 0.16


def _tokens(text: str):
    """解析 ^{...} / _{...} 上下标标记。"""
    toks, buf, i = [], "", 0
    while i < len(text):
        ch = text[i]
        if ch in "^_" and i + 1 < len(text) and text[i + 1] == "{":
            j = text.index("}", i + 2)
            if buf:
                toks.append(("n", buf))
                buf = ""
            toks.append(("sup" if ch == "^" else "sub", text[i + 2:j]))
            i = j + 1
        else:
            buf += ch
            i += 1
    if buf:
        toks.append(("n", buf))
    return toks


def _sub_font(kind, size_final):
    scale = 1.0 if kind == "n" else (SUP_SCALE if kind == "sup" else SUB_SCALE)
    return F(size_final * scale)


def text_width(text: str, size_final: float) -> float:
    return sum(_sub_font(k, size_final).getlength(t) for k, t in _tokens(text))


def draw_text(draw, x, y, text, size_final, fill=BLACK, anchor="l", valign="baseline"):
    """anchor: l/c/r；valign: baseline/top/center。支持 ^{}  _{} 上下标。"""
    size = size_final * S
    w = text_width(text, size_final)
    if anchor == "c":
        x -= w / 2
    elif anchor == "r":
        x -= w
    asc, desc = F(size_final).getmetrics()
    if valign == "top":
        base = y + asc
    elif valign == "center":
        base = y + (asc - desc) / 2
    else:
        base = y
    cx = x
    for kind, t in _tokens(text):
        f = _sub_font(kind, size_final)
        dy = -SUP_RISE * size if kind == "sup" else (SUB_DROP * size if kind == "sub" else 0)
        draw.text((cx, base + dy), t, font=f, fill=fill, anchor="ls")
        cx += f.getlength(t)
    return w


def draw_text_rotated(cv, cx, cy, text, size_final, fill=BLACK, angle=90):
    size = size_final * S
    w = int(text_width(text, size_final)) + 12
    asc, desc = F(size_final).getmetrics()
    h = int((asc + desc) * 1.25)
    tmp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    base = (h + asc - desc) / 2
    cx0 = 6.0
    for kind, t in _tokens(text):
        f = _sub_font(kind, size_final)
        dy = -SUP_RISE * size if kind == "sup" else (SUB_DROP * size if kind == "sub" else 0)
        td.text((cx0, base + dy), t, font=f, fill=fill + (255,), anchor="ls")
        cx0 += f.getlength(t)
    tmp = tmp.rotate(angle, expand=True, resample=Image.BICUBIC)
    cv.img.paste(tmp, (int(cx - tmp.width / 2), int(cy - tmp.height / 2)), tmp)


def dashed_line(draw, p1, p2, fill, width, dash=16, gap=11):
    """按成品像素给定 dash/gap 的虚线。"""
    x1, y1 = p1
    x2, y2 = p2
    dist = math.hypot(x2 - x1, y2 - y1)
    if dist < 1e-6:
        return
    ux, uy = (x2 - x1) / dist, (y2 - y1) / dist
    d, g = dash * S, gap * S
    t = 0.0
    while t < dist:
        t2 = min(t + d, dist)
        draw.line([(x1 + ux * t, y1 + uy * t), (x1 + ux * t2, y1 + uy * t2)],
                  fill=fill, width=width)
        t = t2 + g


def arrow(draw, p_from, p_to, fill=BLACK, width=2 * S, head=13):
    """从 p_from 指向 p_to 的箭头（坐标为设备像素）。"""
    draw.line([p_from, p_to], fill=fill, width=width)
    ang = math.atan2(p_to[1] - p_from[1], p_to[0] - p_from[0])
    h = head * S
    a1 = ang + math.radians(153)
    a2 = ang - math.radians(153)
    p1 = (p_to[0] + h * math.cos(a1), p_to[1] + h * math.sin(a1))
    p2 = (p_to[0] + h * math.cos(a2), p_to[1] + h * math.sin(a2))
    draw.polygon([p_to, p1, p2], fill=fill)


def square(draw, cx, cy, half, fill, outline=None):
    draw.rectangle([cx - half, cy - half, cx + half, cy + half], fill=fill, outline=outline)


class Chart:
    """白底 + 黑色细边框 + 刻度 + 浅灰虚线网格 的坐标轴容器。"""

    def __init__(self, height_final=1100, left=210, right=95, top=120, bottom=175):
        self.Wf, self.Hf = W_FINAL, height_final
        self.img = Image.new("RGB", (self.Wf * S, self.Hf * S), "white")
        self.d = ImageDraw.Draw(self.img)
        self.L, self.T = left * S, top * S
        self.R, self.B = (self.Wf - right) * S, (self.Hf - bottom) * S

    def set_lim(self, xlim, ylim):
        self.x0, self.x1 = xlim
        self.y0, self.y1 = ylim

    def X(self, x):
        return self.L + (x - self.x0) / (self.x1 - self.x0) * (self.R - self.L)

    def Y(self, y):
        return self.B - (y - self.y0) / (self.y1 - self.y0) * (self.B - self.T)

    def frame(self, xticks, yticks, xfmt=str, yfmt=str, title="", xlabel="", ylabel="",
              tick_size=30, label_size=36, title_size=46, grid=True, xlabel_push=0):
        d = self.d
        Lf, Rf, Tf, Bf = self.L / S, self.R / S, self.T / S, self.B / S
        tl = 12                                    # 刻度线长（成品 px）
        # ---- 网格 ----
        if grid:
            for xt in xticks:
                px = self.X(xt)
                dashed_line(d, (px, self.T), (px, self.B), LIGHT, 1 * S, 12, 10)
            for yt in yticks:
                py = self.Y(yt)
                dashed_line(d, (self.L, py), (self.R, py), LIGHT, 1 * S, 12, 10)
        # ---- 边框 ----
        d.rectangle([self.L, self.T, self.R, self.B], outline=BLACK, width=2 * S)
        # ---- 刻度线 + 刻度值 ----
        tick_top = Bf + tl + 11
        for xt in xticks:
            px = self.X(xt)
            d.line([(px, self.B), (px, self.B + tl * S)], fill=BLACK, width=2 * S)
            draw_text(d, px, tick_top * S, xfmt(xt), tick_size, anchor="c", valign="top")
        ylabs = [yfmt(t) for t in yticks]
        tw_max = max(text_width(t, tick_size) for t in ylabs)
        for yt, lb in zip(yticks, ylabs):
            py = self.Y(yt)
            d.line([(self.L - tl * S, py), (self.L, py)], fill=BLACK, width=2 * S)
            draw_text(d, (Lf - tl - 10) * S, py, lb, tick_size, anchor="r", valign="center")
        # ---- 轴标题 ----
        xlab_top = tick_top + tick_size * 1.40 + 22 + xlabel_push
        draw_text(d, (Lf + Rf) / 2 * S, xlab_top * S, xlabel, label_size, anchor="c", valign="top")
        asc, desc = F(label_size).getmetrics()
        rot_h = (asc + desc) * 1.25 / S               # 旋转后文字高度（成品 px）
        ylab_cx = Lf - tl - 10 - tw_max - 24 - rot_h / 2
        draw_text_rotated(self, ylab_cx * S, (Tf + Bf) / 2 * S, ylabel, label_size)
        # ---- 图标题 ----
        if title:
            draw_text(d, (Lf + Rf) / 2 * S, 42 * S, title, title_size, anchor="c", valign="top")

    def data_to_px(self, x, y):
        return self.X(x), self.Y(y)

    def legend(self, x_final, y_final, entries, size=30, anchor="lt"):
        """entries: [(label, color, style, marker)]；style: 'line'/'dashed'；marker: None/'o'/'s'。"""
        d = self.d
        row_h = size * 1.95 * S
        pad = 14 * S
        sample_w = 86 * S
        gap = 16 * S
        tw = max(text_width(lb, size) for lb, *_ in entries)
        box_w = pad + sample_w + gap + tw + pad
        box_h = pad + row_h * len(entries) + pad - row_h * 0.45
        x, y = x_final * S, y_final * S
        if anchor == "rt":
            x -= box_w
        d.rectangle([x, y, x + box_w, y + box_h], fill="white", outline=BLACK, width=2 * S)
        for k, (label, color, style, marker) in enumerate(entries):
            cy = y + pad + row_h * (k + 0.5)
            x1, x2 = x + pad, x + pad + sample_w
            if style == "line":
                d.line([(x1, cy), (x2, cy)], fill=color, width=4 * S)
            else:
                dashed_line(d, (x1, cy), (x2, cy), color, 4 * S, 20, 13)
            if marker == "o":
                r = 7 * S
                d.ellipse([(x1 + x2) / 2 - r, cy - r, (x1 + x2) / 2 + r, cy + r], fill=color)
            elif marker == "s":
                square(d, (x1 + x2) / 2, cy, 7 * S, color)
            draw_text(d, x2 + gap, cy, label, size, valign="center")
        return box_w, box_h

    def notebox(self, x_final, y_final, lines, size=29, anchor="lt", fill="white"):
        """带黑框的注释块；lines 为字符串列表。"""
        d = self.d
        pad_x, pad_y, lh = 18 * S, 14 * S, size * 1.62 * S
        tw = max(text_width(t, size) for t in lines)
        box_w = tw + 2 * pad_x
        box_h = lh * len(lines) + 2 * pad_y - lh * 0.28
        x, y = x_final * S, y_final * S
        if anchor == "rt":
            x -= box_w
        d.rectangle([x, y, x + box_w, y + box_h], fill=fill, outline=BLACK, width=2 * S)
        for k, t in enumerate(lines):
            draw_text(d, x + pad_x, y + pad_y + lh * (k + 0.5) + 2 * S, t, size,
                      valign="center")
        return box_w, box_h

    def save(self, path):
        out = self.img.resize((self.Wf, self.Hf), Image.LANCZOS)
        path.parent.mkdir(parents=True, exist_ok=True)
        out.save(path, "PNG", optimize=True, dpi=(300, 300))   # 1725 px @300 dpi = 14.6 cm
        return path


# --------------------------------------------------------------------------
# 4. 三张图
# --------------------------------------------------------------------------
def fig_va(data):
    t1 = data["tables"]["table1"]
    cv = Chart(height_final=1100, left=215, right=95, top=120, bottom=175)
    cv.set_lim((-4, 30), (0, 70))
    cv.frame(
        xticks=[-4, 0, 5, 10, 15, 20, 25, 30],
        yticks=[0, 10, 20, 30, 40, 50, 60, 70],
        xfmt=lambda v: f"{v:g}",
        yfmt=lambda v: f"{v:g}",
        title="光电管的伏安特性曲线",
        xlabel="U_{AK} / V",
        ylabel="I / 10^{-11} A",
    )
    d = cv.d
    styles = [
        (BLUE, "435.8 nm，Φ = 2 mm"),
        (RED, "546.1 nm，Φ = 4 mm"),
    ]
    # 饱和值辅助线
    for s, (col, _) in zip(t1, styles):
        im = s["I"][-1]
        dashed_line(d, (cv.X(20), cv.Y(im)), (cv.X(30), cv.Y(im)), (170, 170, 170), 2 * S, 14, 12)

    for s, (col, _) in zip(t1, styles):
        pts = [(cv.X(u), cv.Y(i)) for u, i in zip(s["U_AK_V"], s["I"])]
        d.line(pts, fill=col, width=4 * S, joint="curve")
        r = 6.5 * S
        for (px, py) in pts:
            d.ellipse([px - r, py - r, px + r, py + r], fill=col)

    # 图例（左上空白区）
    cv.legend(255, 165, [
        ("435.8 nm，Φ = 2 mm", BLUE, "line", "o"),
        ("546.1 nm，Φ = 4 mm", RED, "line", "o"),
    ], size=30)

    # 上升沿标注
    tx, ty = cv.data_to_px(9.0, 5.5)
    draw_text(d, tx, ty, "上升沿（0 V 附近）", 29, valign="center")
    arrow(d, (tx - 10 * S, ty), cv.data_to_px(1.05, 9.2), width=2 * S)

    # 饱和区标注（两曲线之间的空白带）
    sx, sy = cv.data_to_px(22.5, 52.0)
    draw_text(d, sx, sy, "饱和区", 30, valign="center")
    arrow(d, (sx + 96 * S, sy - 6 * S), cv.data_to_px(28.0, 45.9), width=2 * S)

    # 右下角数据说明（该区域两条曲线均无点）
    im435 = t1[0]["I"][-1]
    im546 = t1[1]["I"][-1]
    cv.notebox(1010, 695, [
        f"U_{{AK}} = 30 V 时饱和电流",
        f"I_{{M}} = {im435:g} × 10^{{-11}} A（435.8 nm）",
        f"I_{{M}} = {im546:g} × 10^{{-11}} A（546.1 nm）",
    ], size=28)
    return cv.save(FIGDIR / "fig_va.png")


def _clip_segment(x0, x1, y0, y1, ylim):
    """把直线段裁剪到 ylim 内（用于拟合线）。"""
    lo, hi = ylim
    pts = []
    for xa, ya in ((x0, y0), (x1, y1)):
        if lo <= ya <= hi:
            pts.append((xa, ya))
    if y1 != y0:
        for yb in (lo, hi):
            if min(y0, y1) < yb < max(y0, y1):
                t = (yb - y0) / (y1 - y0)
                pts.append((x0 + t * (x1 - x0), yb))
    pts.sort()
    if len(pts) >= 2:
        return pts[0], pts[-1]
    return None


def fig_u0nu(data):
    u0 = data["u0_avg"]
    fit = data["fit"]["with_intercept"]
    nu = u0["nu_1014Hz"]
    us = u0["U_s_V"]
    cv = Chart(height_final=1100, left=205, right=95, top=120, bottom=175)
    cv.set_lim((5.0, 8.5), (0.0, 1.6))
    cv.frame(
        xticks=[5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5],
        yticks=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6],
        xfmt=lambda v: f"{v:.1f}",
        yfmt=lambda v: f"{v:.1f}",
        title="截止电压与入射光频率的关系",
        xlabel="ν / 10^{14} Hz",
        ylabel="U_{s} = |U_{0}| / V",
    )
    d = cv.d

    # 拟合直线
    a14 = fit["slope_a14_V_per_1e14Hz"]
    b = fit["intercept_b_V"]
    seg = _clip_segment(5.0, 8.5, a14 * 5.0 + b, a14 * 8.5 + b, (0.0, 1.6))
    if seg:
        dashed_line(d, cv.data_to_px(*seg[0]), cv.data_to_px(*seg[1]), GREEN, 4 * S, 22, 14)

    # 数据点（实心方块）+ λ 标注（默认右下偏移；贴边/压线处改方位）
    hw = 7.5 * S
    lam = data["tables"]["table3"]["lambda_nm"]
    lam_off = {
        365.0: (-12, 10, "r"),     # 右下会越出右框 → 改左下方
        404.7: (12, 10, "l"),      # 右下方，避开拟合虚线
        435.8: (12, 10, "l"),
        546.1: (12, 10, "l"),
        577.0: (-64, -48, "l"),    # 左侧贴框且压线 → 移到该点正上方
    }
    for la, xv, yv in zip(lam, nu, us):
        px, py = cv.data_to_px(xv, yv)
        square(d, px, py, hw, BLACK)
        ox, oy, an = lam_off[la]
        draw_text(d, px + ox * S, py + oy * S, f"{la:.1f} nm", 26,
                  fill=(70, 70, 70), anchor=an, valign="top")

    # 图例（右下空白）
    cv.legend(1610, 790, [
        ("测量点（三次平均）", BLACK, "line", "s"),
        ("最小二乘拟合直线", GREEN, "dashed", None),
    ], size=30, anchor="rt")

    # 拟合结果注释（左上空白）
    K = fit["slope_K_Vs"]
    h34 = fit["h_1e34"]
    r2 = fit["r2"]
    err = fit["rel_err_pct"]
    a_txt = f"{a14:.4f}"
    b_abs = abs(b)
    sign = "−" if b < 0 else "+"
    cv.notebox(320, 160, [
        f"U_{{s}} = {a_txt}ν {sign} {b_abs:.3f}   (ν 以 10^{{14}} Hz 计)",
        f"K = {K / 1e-15:.4f} × 10^{{-15}} V·s，b = {b:.3f} V",
        f"h = eK = {h34:.3f} × 10^{{-34}} J·s（相对误差 {err:.1f}%）",
        f"逸出功 A_{{s}} = e|b| = {fit['work_function_eV']:.3f} eV",
        f"R^{{2}} = {r2:.4f}，r = {fit['r']:.4f}",
    ], size=28)
    return cv.save(FIGDIR / "fig_u0nu.png")


def fig_ip(data):
    t2 = data["table2_check"]["series"]
    cv = Chart(height_final=1100, left=205, right=95, top=120, bottom=215)
    cv.set_lim((0, 70), (0, 750))
    cv.frame(
        xticks=[0, 10, 20, 30, 40, 50, 60, 70],
        yticks=[0, 100, 200, 300, 400, 500, 600, 700],
        xfmt=lambda v: f"{v:g}",
        yfmt=lambda v: f"{v:g}",
        title="饱和电流与光阑孔面积的关系",
        xlabel="Φ^{2} / mm^{2}   （Φ 为光阑孔径）",
        ylabel="I_{M} / 10^{-11} A",
        xlabel_push=34,
    )
    d = cv.d
    # 横轴下方补充 Φ 对应值（2 / 4 / 8 mm）
    phi_row_y = cv.B / S + 12 + 11 + 30 * 1.40 + 6
    for phi, p2 in ((2, 4), (4, 16), (8, 64)):
        px = cv.X(p2)
        draw_text(d, px, phi_row_y * S, f"Φ={phi}", 26, fill=(95, 95, 95),
                  anchor="c", valign="top")

    styles = [(BLUE, "435.8 nm"), (RED, "546.1 nm")]
    for s, (col, _) in zip(t2, styles):
        pts = [(cv.X(p2), cv.Y(im)) for p2, im in zip(s["phi2_mm2"], s["I_M"])]
        d.line(pts, fill=col, width=4 * S, joint="curve")
        r = 7 * S
        for (px, py) in pts:
            d.ellipse([px - r, py - r, px + r, py + r], fill=col)

    # 数据点数值标注：曲线同色文字；贴边/拥挤处用短引线
    tags = [
        # p2, I_M, 文本, dx, dy, anchor, valign, 颜色, 引线(起,止 相对数据点) 或 None
        (4, 46.8, "46.8", -14, 0, "r", "center", BLUE, None),
        (16, 173.0, "173.0", -40, -30, "r", "center", BLUE, (-40, -30, -9, -9)),
        (64, 687.0, "687.0", -16, -4, "r", "bottom", BLUE, None),
        (4, 18.0, "18.0", 94, -75, "l", "top", RED, (94, -57, 7, -7)),
        (16, 65.6, "65.6", 12, -28, "l", "bottom", RED, None),
        (64, 256.8, "256.8", 12, 17, "l", "top", RED, None),
    ]
    for p2, im, txt, dx, dy, an, val, col, lead in tags:
        px, py = cv.data_to_px(p2, im)
        tx, ty = px + dx * S, py + dy * S
        draw_text(d, tx, ty, txt, 28, fill=col, anchor=an, valign=val)
        if lead:
            sx, sy, ex, ey = lead
            d.line([(px + sx * S, py + sy * S), (px + ex * S, py + ey * S)],
                   fill=col, width=2 * S)

    cv.legend(240, 165, [
        ("435.8 nm，Φ = 2/4/8 mm", BLUE, "line", "o"),
        ("546.1 nm，Φ = 2/4/8 mm", RED, "line", "o"),
    ], size=29)

    s435, s546 = t2[0], t2[1]
    cv.notebox(1540, 420, [
        "归一化 I_{M}（理论 1 : 4 : 16）",
        f"435.8 nm：1 : {s435['normalized_I_M'][1]:.2f} : {s435['normalized_I_M'][2]:.2f}",
        f"546.1 nm：1 : {s546['normalized_I_M'][1]:.2f} : {s546['normalized_I_M'][2]:.2f}",
        "I_{M} ∝ 光强 ∝ Φ^{2}",
    ], size=26, anchor="rt")
    return cv.save(FIGDIR / "fig_ip.png")


# --------------------------------------------------------------------------
# 5. 入口
# --------------------------------------------------------------------------
def main():
    data = build_data()
    FIGDIR.mkdir(parents=True, exist_ok=True)

    for name in ("fig_va.png", "fig_u0nu.png", "fig_ip.png"):
        p = FIGDIR / name
        if p.exists():
            p.unlink()

    p1 = fig_va(data)
    p2 = fig_u0nu(data)
    p3 = fig_ip(data)

    (ROOT / "data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    f = data["fit"]["with_intercept"]
    fo = data["fit"]["through_origin"]
    print("== 已完成 ==")
    print(f"data.json           : {ROOT / 'data.json'}")
    for p in (p1, p2, p3):
        im = Image.open(p)
        print(f"{p.name:<20}: {p}  {im.size[0]}x{im.size[1]} px")
    print("\n== 拟合（带截距，主结果）==")
    print(f"U0 平均 : {data['u0_avg']['U0_avg_V']}")
    print(f"a14     : {f['slope_a14_V_per_1e14Hz']} V/(1e14 Hz)")
    print(f"K       : {f['slope_K_Vs']:.6e} V*s")
    print(f"b       : {f['intercept_b_V']} V")
    print(f"r / R2  : {f['r']} / {f['r2']}")
    print(f"h       : {f['h_Js']:.6e} J*s  相对误差 {f['rel_err_pct']:.3f}%")
    print("\n== 过原点对照 ==")
    print(f"K0      : {fo['slope_K_Vs']:.6e} V*s  "
          f"h0 = {fo['h_Js']:.6e} J*s  相对误差 {fo['rel_err_pct']:.1f}%  R2 = {fo['r2']}")
    print("\n== 表2 ==")
    for s in data["table2_check"]["series"]:
        print(f"{s['lambda_nm']} nm: 归一化 {s['normalized_I_M']}  偏差 {s['deviation_pct']} %")
    print("\n== 表1 ==")
    for s in data["table1_analysis"]["series"]:
        print(f"{s['lambda_nm']} nm: I_M(30V)={s['I_at_30V']}  "
              f"20->30V 变化 {s['saturation_rel_change_20_30V_pct']:.2f}%  "
              f"10V 时已完成 {s['rise_completed_by_10V_pct']:.1f}%")


if __name__ == "__main__":
    main()
