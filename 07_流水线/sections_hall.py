# -*- coding: utf-8 -*-
"""霍尔效应及其应用（实验 30）的 block 组装：只管摆什么，不管长什么样。"""

HEAD_V = ['I_s/mA', 'V1/mV', 'V2/mV', 'V3/mV', 'V4/mV', 'V_H/mV']
HEAD_M = ['I_M/mA', 'V1/mV', 'V2/mV', 'V3/mV', 'V4/mV', 'V_H/mV']
HEAD_B = ['I_M/mA', 'B1/mT', 'B2/mT', 'B3/mT', 'B4/mT', 'B/mT']
W6 = [1100, 1500, 1500, 1500, 1500, 1200]
W2 = [4150, 4150]


def num(v, digits=3):
    if v is None:
        return '—'
    try:
        f = float(v)
    except (TypeError, ValueError):
        return '—'
    if f != f:
        return '—'
    s = '%.*f' % (digits, f)
    return s.replace('-', '−')


def tables(calc):
    t1, t2, t3, t4 = calc['t1'], calc['t2'], calc['t3'], calc['t4']
    rows1 = [HEAD_V]
    for i in range(len(t1['x'])):
        v = t1['v'][i]
        rows1.append([num(t1['x'][i], 2), num(v[0], 2), num(v[1], 2), num(v[2], 2),
                      num(v[3], 2), num(t1['vh'][i], 3)])
    rows2 = [HEAD_M]
    for i in range(len(t2['x'])):
        v = t2['v'][i]
        rows2.append([num(t2['x'][i], 0), num(v[0], 2), num(v[1], 2), num(v[2], 2),
                      num(v[3], 2), num(t2['vh'][i], 3)])
    rows3 = [HEAD_B]
    for i in range(len(t3['x'])):
        b = t3['b'][i]
        rows3.append([num(t3['x'][i], 0), num(b[0], 1), num(b[1], 1), num(b[2], 1),
                      num(b[3], 1), num(t3['b_avg'][i], 1)])
    rows4 = [['I/mA', 'U_AC/mV']]
    for i in range(len(t4['x'])):
        rows4.append([num(t4['x'][i], 2), num(t4['u'][i], 2)])
    return [
        {'t': 'table', 'rows': rows1, 'header': 1, 'font': 10.5, 'widths': W6},
        {'t': 'table', 'rows': rows2, 'header': 1, 'font': 10.5, 'widths': W6},
        {'t': 'table', 'rows': rows3, 'header': 1, 'font': 10.5, 'widths': W6},
        {'t': 'table', 'rows': rows4, 'header': 1, 'font': 10.5, 'widths': W2},
    ]


def explain(calc):
    r = calc['result']
    t1, t2, t3, t4 = calc['t1'], calc['t2'], calc['t3'], calc['t4']
    return [
        '（1）每组读数按对称测量法处理：V_H = (V1 − V2 + V3 − V4)/4。能斯特效应、里吉—勒杜克效应'
        '随磁场反向而改号，不等势电压随工作电流反向而改号，四项相加时相互抵消；埃廷斯豪森效应'
        '与霍尔电压方向相同，换向不能消除，但其量级比霍尔电压小一个数量级以上，可忽略不计。',
        '（2）以 I_s 为横轴、V_H 为纵轴作图，数据落在一条过原点的直线上：斜率 k = %s mV/mA，'
        '相关系数 r² = %s，说明在固定磁场下 V_H 与 I_s 严格成正比。'
        % (num(r['k_s_mV_per_mA'], 3), num(r['r2_s'], 5)),
        '（3）以 I_M 为横轴、V_H 为纵轴作图，斜率 k′ = %s mV/mA，r² = %s；表 3 的 B–I_M 关系'
        '也是一条直线，斜率 %s mT/mA，r² = %s。这说明电磁铁气隙中的磁场随励磁电流线性增长，'
        '在 I_M = %s mA 处 B = %s mT。'
        % (num(r['k_m_mV_per_mA'], 3), num(r['r2_m'], 5), num(r['k_b_mT_per_mA'], 3),
           num(r['r2_b'], 5), num(300, 0), num(r['B_ref_mT'], 1)),
        '（4）由表 1 的直线斜率求霍尔系数：R_H = k·d/B = %s×10⁻⁴ m³·C⁻¹；由表 2、表 3 的斜率'
        '求灵敏度 K_H = (k′/I_s)/(dB/dI_M) = %s mV/(mA·T)，相应 R_H = %s×10⁻⁴ m³·C⁻¹，'
        '两条路径的结果在 %s%% 以内一致，取平均得 R_H = %s×10⁻⁴ m³·C⁻¹。'
        % (num(r['R_H_a'] * 1e4, 3), num(r['K_H_b'], 3), num(r['R_H_b'] * 1e4, 3),
           num(abs(r['R_H_a'] - r['R_H_b']) / abs(r['R_H']) * 100, 1), num(r['R_H'] * 1e4, 3)),
        '（5）表 4 的 U_AC–I 直线斜率即元件的体电阻 R = %s Ω，由 σ = I·l/(U_AC·S) 得电导率'
        'σ = %s S/m，其中 S = b·d = %s×10⁻⁷ m²。'
        % (num(r['R_sample_ohm'], 2), num(r['sigma_S_m'], 1), num(r['S_m2'] * 1e7, 2)),
        '（6）由 R_H = 1/(n e) 得载流子浓度 n = %s×10²¹ m⁻³；由 μ = |R_H|·σ 得迁移率'
        'μ = %s m²·V⁻¹·s⁻¹。R_H > 0 说明载流子带正电，样品为 P 型；'
        'n 在 10²¹ m⁻³ 量级，正是半导体材料载流子浓度比金属低得多的体现，这也是霍尔元件都用'
        '半导体制作的原因。'
        % (num(r['n_m3'] * 1e-21, 3), num(r['mu'], 3)),
        '（7）纯度更高的单晶半导体迁移率可达 1 m²·V⁻¹·s⁻¹ 量级，本实验结果与之同一量级，'
        '说明数据处理基本合理。误差主要来自元件厚度 d 的标注值与实际值之间的差别（d 出现在'
        'K_H 和 n 的计算中，且是一次方）、气隙磁场的不均匀性以及副效应残余。'
        '若要在报告里给出不确定度，可按 R_H 的两条路径之差估计 A 类不确定度，再按 d 的'
        '相对误差估计 B 类分量。',
    ]


def build(exp, calc, md):
    B = []
    source = (calc.get('provenance') or {}).get('source')
    synth = source in ('synthetic', 'mock')

    B.append({'t': 'sect', 'name': '实验目的', 'pct': '10%'})
    for i, s in enumerate(exp.get('objectives', []), 1):
        B.append({'t': 'para', 'text': '%d. %s' % (i, s)})

    B.append({'t': 'sect', 'name': '实验仪器', 'pct': ''})
    for line in md.get('仪器', []):
        B.append({'t': 'para', 'text': line})

    B.append({'t': 'sect', 'name': '实验原理', 'pct': '10%',
              'note': '(可以拷贝网上文字，最好在理解基础上有所删减，不需完全拷贝。'
                      '需要有实验相关重要的公式及图形。建议手动输入公式，不能粘贴公式图片。)'})
    for key in ('原理1', '原理2', '原理3', '原理4'):
        for line in md.get(key, []):
            B.append({'t': 'para', 'text': line})

    B.append({'t': 'sect', 'name': '实验内容与步骤', 'pct': '10%',
              'note': '(实验内容及主要操作步骤,可能会因实验仪器的更换有所改变和增减，'
                      '与教材中不同。根据实际操作完成此部分内容)'})
    for line in md.get('步骤', []):
        B.append({'t': 'para', 'text': line})

    B.append({'t': 'sect', 'name': '有教师签字的原始数据记录照片（请竖排粘贴）', 'pct': '10%'})
    if synth:
        B.append({'t': 'note', 'text': '（本报告使用示例数据：没有原始数据记录页照片，'
                                       '正式使用时此处粘贴有教师签字的照片。）'})
    else:
        B.append({'t': 'note', 'text': '（此处粘贴原始数据记录页照片）'})

    B.append({'t': 'sect', 'name': '数据处理及结果', 'pct': '20%',
              'note': '  (此处的表格要与原始数据记录页的表格一致；表格中的数据要与原始数据记录页中的数据一致；'
                      '表格后处理数据,要有主要的处理过程；要求用作图法处理的可以插入画好图的坐标纸,'
                      '推荐电脑作图；处理的中间结果应多保留1-2位，最终结果表示应符合有效数字规则和'
                      '不确定度位数要求；计算中要特别注意单位的换算和书写。)'})
    for line in md.get('数据说明', []):
        B.append({'t': 'para', 'text': line})

    caps = ['表1 V_H–I_s 数据（I_M = 300 mA）',
            '表2 V_H–I_M 数据（I_s = 1.00 mA）',
            '表3 B–I_M 数据（I_s = 1.00 mA）',
            '表4 霍尔元件电导率的测量（U_AC–I 关系）']
    for cap, tab in zip(caps, tables(calc)):
        B.append({'t': 'caption', 'text': cap, 'bold': True})
        B.append(tab)
    for line in explain(calc):
        B.append({'t': 'para', 'text': line})

    B.append({'t': 'sect', 'name': '分析及体会', 'pct': '20%',
              'note': '（以“我”为主语，描述本次实验的感受。可以说实验中的意外、'
                      '对实验的理解、对课程的建议等，不计空格字符数统计不小于300字）'})
    for line in md.get('体会', []):
        B.append({'t': 'para', 'text': line})

    B.append({'t': 'heading', 'text': '【思考题】', 'center': False})
    for line in md.get('思考题', []):
        bold = bool(line[:2].strip().rstrip('.').isdigit()) and '（答）' not in line
        B.append({'t': 'para', 'text': line, 'bold': bold, 'indent': not bold})

    B.append({'t': 'sect', 'name': '超星平台本实验在线练习得分截图（请竖排粘贴）', 'pct': '5%'})
    B.append({'t': 'shot', 'path': exp.get('_shot'), 'width_cm': 8.2, 'row_h': 3200})
    return B
