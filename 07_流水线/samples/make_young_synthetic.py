# -*- coding: utf-8 -*-
"""生成「杨氏模量」实验的**合成示例数据**（固定数值、可复现，非实测）。

用途：在拿到真实原始数据之前，验证流水线能不能吃下第二种处理范式（逐差法）。
所有数值都是按物理关系反推的合理值，写进 data 时 provenance.source = 'synthetic'，
报表与页面上必须显示「示例数据」标记，不能当成实测结果提交。

物理自洽：Y = 8FLD/(πd²K·N̄)，取钢丝 Y≈2.0×10¹¹ Pa 反解每 kg 的标尺读数变化。
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))

G = 9.794                     # 南京地区重力加速度 m/s^2
M0 = 2.000                    # 初始砝码 kg
STEP = 1.000                  # 每次加 1 kg，共加 7 次
D_M = 1.500                   # 镜面到标尺距离 m
L_M = 1.000                   # 上下夹子间钢丝长度 m
K_M = 0.0750                  # 光杠杆臂长 m
ZERO_MM = 0.002               # 千分尺零点读数 mm

# 标尺读数（单位 10^-2 m，即 cm），增重 / 减重各一组
UP = [10.00, 12.79, 15.57, 18.36, 21.13, 23.92, 26.70, 29.48]
DOWN = [10.03, 12.82, 15.60, 18.39, 21.17, 23.95, 26.73, 29.51]

# 钢丝直径 6 次（mm）
DIA = [0.298, 0.301, 0.299, 0.302, 0.300, 0.301]


def main():
    n = [(a + b) / 2.0 for a, b in zip(UP, DOWN)]
    Ns = [round(n[i + 4] - n[i], 3) for i in range(4)]
    N_bar = sum(Ns) / 4.0                       # cm
    s = math.sqrt(sum((x - N_bar) ** 2 for x in Ns) / 3.0)
    s_nbar = s / 2.0

    d_bar = sum(DIA) / len(DIA)                 # mm
    d_true = d_bar - ZERO_MM                    # mm（修正后）
    d_m = d_true * 1e-3
    F = 4.0 * G                                 # 每 4 kg 对应的拉力 N
    N_m = N_bar * 1e-2

    Y = 8 * F * L_M * D_M / (math.pi * d_m ** 2 * K_M * N_m)

    # 不确定度（相对合成）
    u_d = math.sqrt((0.004) ** 2 + (s / math.sqrt(len(DIA)) if False else 0) ** 2)  # 千分尺 Δ仪
    s_d = math.sqrt(sum((x - d_bar) ** 2 for x in DIA) / (len(DIA) - 1))
    u_d_tot = math.sqrt((0.004 / 1e3) ** 2 + (s_d / math.sqrt(6) / 1e3) ** 2)
    rel = {
        'd': 2 * u_d_tot / d_m,
        'K': 0.0005 / K_M,
        'D': 0.002 / D_M,
        'L': 0.0005 / L_M,
        'F': (0.020 * G) / F,
        'N': (s_nbar * 1e-2) / N_m,
    }
    rel_tot = math.sqrt(sum(v ** 2 for v in rel.values()))
    u_Y = rel_tot * Y

    out = {
        'exp': 'young',
        'provenance': {
            'source': 'synthetic',
            'note': '按 Y≈2.0×10^11 Pa 反推的示例数据，仅用于验证流水线与排版，不是实测值',
            'generator': 'samples/make_young_synthetic.py',
        },
        'constants': {'g': G},
        'tables': {
            't1': {
                'm_kg': [M0 + STEP * i for i in range(8)],
                'n_up_cm': UP, 'n_down_cm': DOWN, 'n_mean_cm': [round(x, 3) for x in n],
                'N_cm': Ns, 'N_bar_cm': round(N_bar, 4), 'S_N_cm': round(s, 4),
                'S_Nbar_cm': round(s_nbar, 4),
            },
            't2': {'d_mm': DIA, 'zero_mm': ZERO_MM,
                   'd_bar_mm': round(d_bar, 4), 'd_fixed_mm': round(d_true, 4),
                   'S_d_mm': round(s_d, 4)},
            't3': {'D_m': D_M, 'u_D_m': 0.002, 'L_m': L_M, 'u_L_m': 0.0005,
                   'K_m': K_M, 'u_K_m': 0.0005, 'u_m_kg': 0.005},
        },
        'calc': {
            'F_N': F, 'N_bar_m': round(N_m, 6),
            'Y_Pa': Y, 'Y_display': Y,
            'relative_uncertainty': rel_tot, 'u_Y_Pa': u_Y,
            'components': rel,
            'accepted_Pa': 2.0e11,
            'rel_err_pct': (Y - 2.0e11) / 2.0e11 * 100.0,
            'magnification': 2 * D_M / K_M,
        },
    }
    p = os.path.join(HERE, 'young_synthetic.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print('Y = %.4e Pa  (%.3e ×10^11)  rel.u = %.3f%%  err = %+.2f%%'
          % (Y, Y / 1e11, rel_tot * 100, out['calc']['rel_err_pct']))
    print('N_bar = %.4f cm  S = %.4f cm  d = %.4f mm  → %s' % (N_bar, s, d_true, p))


if __name__ == '__main__':
    main()
