# -*- coding: utf-8 -*-
"""光电效应（实验 47）报告的 block 组装。

和 sections_young.py 一样：只决定「摆什么」，长什么样交给 render_docx.py。
"""


def num(v, digits=4):
    return ('%.*f' % (digits, v)).replace('-', '−')


import os

GEN = os.environ.get('PIPE_GEN',
                     r'C:\Users\lidey\Desktop\实验报告制作沙盒\04_生成过程_脚本图表')
FIG = os.path.join(GEN, 'figures')


def _fig(path, w, cap):
    return {'t': 'figure', 'path': path, 'width_cm': w, 'caption': cap}


def _ap(label):
    """从「435.8 nm / Φ=2 mm」里取出孔径写法「2 mm」。"""
    k = label.find('Φ=')
    if k < 0:
        return ''
    return label[k + 2:].strip()


def _wl(label):
    """「435.8 nm / Φ=2 mm」→「435.8 nm」。"""
    return label.split('/')[0].strip()


def tables(calc):
    """三张表按「直接生成版」的版式复刻：表1 18x10、表2 6x5、表3 6x7。"""
    t1 = calc['t1']['curves']
    W1 = [1250, 1290] + [720] * 8
    rows1, mg1 = [], []
    labels = [(0, 8, 1), (8, 16, 9), (16, 22, 17)]
    for b, (a, z, first) in enumerate(labels):
        base = len(rows1)
        rows1.append(['波长\n光阑', '电压\n电流', '测量数组'] + [''] * 7)
        rows1.append(['', ''] + [str(first + k) if k <= (z - a) else '' for k in range(8)])
        mg1 += [(base, 0, base + 1, 0), (base, 1, base + 1, 1), (base, 2, base, 9)]
        for c in t1:
            u = c['u'][a:z]
            ii = c['i'][a:z]
            rows1.append([_wl(c['label']), 'U_AK (V)'] + [num(x, 0) for x in u] + [''] * (8 - len(u)))
            rows1.append([_ap(c['label']), 'I'] + [num(x, 1) for x in ii] + [''] * (8 - len(ii)))
    T1 = {'t': 'table', 'rows': rows1, 'header': 2, 'font': 9.5, 'widths': W1,
          'merges': mg1, 'bold_col0': False, 'row_h': 380}

    t2 = calc['t2']['rows']
    rows2 = [['波长', '光阑\n电流', '测量数组', '', ''],
             ['', '', '1', '2', '3']]
    mg2 = [(0, 0, 1, 0), (0, 1, 1, 1), (0, 2, 0, 4)]
    for d in t2:
        base = len(rows2)
        rows2.append([d['label'], '光阑孔 Φ', '2 mm', '4 mm', '8 mm'])
        rows2.append(['', 'I（10⁻¹¹ A）', num(d['i2'], 1), num(d['i4'], 1), num(d['i8'], 1)])
        mg2.append((base, 0, base + 1, 0))
    T2 = {'t': 'table', 'rows': rows2, 'header': 2, 'font': 10.5,
          'widths': [1500, 2400, 1470, 1470, 1460], 'merges': mg2, 'bold_col0': False}

    t3 = calc['t3']
    lam, nu, reads = t3['lam'], t3['nu'], t3['reads']
    rows3 = [['波长 λ（nm）', ''] + [num(x, 1) for x in lam],
             ['频率 ν（10¹⁴ Hz）', ''] + [num(x, 3) for x in nu]]
    mg3 = [(0, 0, 0, 1), (1, 0, 1, 1)]
    for k in range(min(3, len(reads))):
        rows3.append(['截止电压\nU_s（V）' if k == 0 else '', str(k + 1)] +
                     [num(x, 3) for x in reads[k]])
    mg3.append((2, 0, 2 + min(3, len(reads)) - 1, 0))
    rows3.append(['U_s 平均值（V）', ''] + [num(x, 3) for x in t3['u0_avg']])
    mg3.append((len(rows3) - 1, 0, len(rows3) - 1, 1))
    T3 = {'t': 'table', 'rows': rows3, 'header': 2, 'font': 10.5,
          'widths': [1900, 600] + [1160] * len(lam), 'merges': mg3, 'bold_col0': False}
    return T1, T2, T3


def explain(calc, exp):
    r = calc['result']
    t2 = calc['t2']['norm']
    lines = [
        '（1）截止电压取三次读数的平均值的绝对值：Uₛ = |Ū₀|。用零电流法判断——'
        '把 U_AK 从 −4 V 缓慢调到 +30 V，电流刚过零点附近要反复微调，那个读数就是 Ū₀，'
        '再取绝对值即得 Uₛ。',
        '（2）作 Uₛ–ν 图，五个点大致落在一条直线上，用最小二乘法拟合得 '
        'Uₛ = %.4fν − %.3f（ν 以 10¹⁴ Hz 计），相关系数 r = %.4f，'
        '说明 Uₛ 确实随 ν 线性变化，这正是爱因斯坦方程 Uₛ = (h/e)ν − Aₛ/e 要求的。'
        % (r['slope_a14'], abs(r['intercept_V']), r['r']),
        '（3）直线斜率 K = %.4e V·s，由 h = eK 得普朗克常量 '
        'h = 1.602×10⁻¹⁹ × %.4e = %.4e J·s。'
        % (r['K_Vs'], r['K_Vs'], r['h']),
        '（4）与公认值 h₀ = 6.626×10⁻³⁴ J·s 相比，相对误差 E = (%.3e − 6.626×10⁻³⁴)/6.626×10⁻³⁴ '
        '= %+.2f%%。' % (r['h'], r['rel_err_pct']),
        '（5）斜率的标准偏差 u(K) = %.3e V·s，于是 u(h) = e·u(K) = %.3e J·s，'
        '结果写作 h = (%.2f ± %.2f)×10⁻³⁴ J·s。' % (r['u_K_Vs'], r['u_h'], r['h'] * 1e34, r['u_h'] * 1e34),
        '（6）截距绝对值 %.3f V 就是逸出功对应的电压，Aₛ = %.3f eV；'
        '令 Uₛ = 0 得红限频率 ν₀ = %.3f×10¹⁴ Hz，对应波长 λ₀ ≈ %.0f nm。'
        % (abs(r['intercept_V']), r['work_eV'], r['nu0_1e14'], r['lam0_nm']),
        '（7）由表 2 验证饱和电流与光强的关系：同一波长下 I_M 与光阑孔面积（Φ²）成正比，'
        '归一化后 %s。' % '；'.join('%s 为 1 : %.2f : %.2f' % (d['label'], d['ratio'][1], d['ratio'][2])
                                    for d in t2) if t2 else '（表 2 未填）',
    ]
    return lines


def build(exp, calc, md):
    B = []
    # 目的
    B.append({'t': 'sect', 'name': '实验目的', 'pct': '10%'})
    for i, s in enumerate(exp.get('objectives', []), 1):
        B.append({'t': 'para', 'text': '%d. %s' % (i, s)})

    # 仪器
    B.append({'t': 'sect', 'name': '实验仪器', 'pct': ''})
    for line in md.get('仪器', []):
        B.append({'t': 'para', 'text': line})
    B.append(_fig(os.path.join(GEN, 'fig_panel.png'), 13.1, '图1 普朗克实验仪前面板示意图'))
    B.append(_fig(os.path.join(GEN, 'fig_wiring.png'), 13.1, '图2 普朗克实验仪结构及接线示意图'))

    # 原理
    B.append({'t': 'sect', 'name': '实验原理', 'pct': '10%',
              'note': '(可以拷贝网上文字，最好在理解基础上有所删减，不需完全拷贝。'
                      '需要有实验相关重要的公式及图形。建议手动输入公式，不能粘贴公式图片。)'})
    for key in ('原理1', '原理2', '原理3', '原理4'):
        for line in md.get(key, []):
            B.append({'t': 'para', 'text': line})
    B.append(_fig(os.path.join(GEN, 'fig_light_path.png'), 11.2,
                  '图3 光电效应实验的光路与测量电路'))

    # 步骤
    B.append({'t': 'sect', 'name': '实验内容与步骤', 'pct': '10%',
              'note': '(实验内容及主要操作步骤,可能会因实验仪器的更换有所改变和增减，'
                      '与教材中不同。根据实际操作完成此部分内容)'})
    for line in md.get('步骤', []):
        B.append({'t': 'para', 'text': line})

    # 原始数据
    B.append({'t': 'sect', 'name': '有教师签字的原始数据记录照片（请竖排粘贴）', 'pct': '10%'})
    src = (calc.get('provenance') or {}).get('source')
    if src == 'photo':
        B.append({'t': 'note', 'text': '（此处粘贴原始数据记录页照片：下表数字即从该照片识别而来。）'})
    else:
        B.append({'t': 'note', 'text': '（本报告使用示例数据：正式使用时此处粘贴有教师签字的照片。）'})

    # 数据处理
    B.append({'t': 'sect', 'name': '数据处理及结果', 'pct': '20%',
              'note': '  (此处的表格要与原始数据记录页的表格一致；表格中的数据要与原始数据记录页中的数据一致；'
                      '表格后处理数据,要有主要的处理过程；要求用作图法处理的可以插入画好图的坐标纸,'
                      '推荐电脑作图；处理的中间结果应多保留1-2位，最终结果表示应符合有效数字规则和'
                      '不确定度位数要求；计算中要特别注意单位的换算和书写。)'})
    for line in md.get('数据说明', []):
        B.append({'t': 'para', 'text': line})

    T1, T2, T3 = tables(calc)
    B.append({'t': 'caption', 'text': '表1 光电管的 U_AK~I_K 关系', 'bold': True})
    B.append(T1)
    B.append(_fig(os.path.join(FIG, 'fig_va.png'), 14.3, '图4 光电管的伏安特性曲线'))
    B.append({'t': 'caption', 'text': '表2 I_M—P 关系（U_AK＝30 V）', 'bold': True})
    B.append(T2)
    B.append(_fig(os.path.join(FIG, 'fig_ip.png'), 14.3, '图5 饱和电流与光阑孔面积的关系'))
    B.append({'t': 'caption', 'text': '表3 U₀~ν 关系测量（Φ＝2 mm）', 'bold': True})
    B.append(T3)
    B.append(_fig(os.path.join(FIG, 'fig_u0nu.png'), 14.3, '图6 截止电压与入射光频率的关系'))
    for line in explain(calc, exp):
        B.append({'t': 'para', 'text': line})

    # 体会
    B.append({'t': 'sect', 'name': '分析及体会', 'pct': '20%',
              'note': '（以“我”为主语，描述本次实验的感受。可以说实验中的意外、'
                      '对实验的理解、对课程的建议等，不计空格字符数统计不小于300字）'})
    for line in md.get('体会', []):
        B.append({'t': 'para', 'text': line})

    # 思考题
    B.append({'t': 'sect', 'name': '思考题', 'pct': ''})
    for line in md.get('思考题', []):
        B.append({'t': 'para', 'text': line})

    # 超星截图位（有截图就贴进去，没有就留提示）
    B.append({'t': 'sect', 'name': '超星平台本实验在线练习得分截图（请竖排粘贴）', 'pct': '5%'})
    B.append({'t': 'shot', 'path': exp.get('_shot'), 'width_cm': 8.2, 'row_h': 3200})
    return B
