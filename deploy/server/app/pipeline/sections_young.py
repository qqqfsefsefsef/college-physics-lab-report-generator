# -*- coding: utf-8 -*-
"""杨氏模量报告的 block 组装（只管「摆什么」，不管「长什么样」）。

渲染细节全部在 render_docx.py；这里只决定顺序、表格内容与计算说明的文字。
"""

SUP = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵',
       '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹', '-': '⁻'}


def sci(v, digits=2):
    """2.02×10¹¹ 这种写法（指数用上标字符，避免字体里没有 10^11 的排版）。"""
    e = 0
    x = abs(v)
    while x >= 10:
        x /= 10.0
        e += 1
    while x < 1:
        x *= 10.0
        e -= 1
    s = '%.*f×10' % (digits, x)
    return s + ''.join(SUP[c] for c in str(e))


def num(v, digits=4):
    s = ('%.*f' % (digits, v))
    return s.replace('-', '−')


def tables(calc):
    t1 = calc['t1']
    rows = [['次数', '荷载 m/kg', '增重 n↑/10⁻²m', '减重 n↓/10⁻²m', '平均 n̄/10⁻²m', 'N/10⁻²m']]
    for i, m in enumerate(t1['m_kg']):
        n = t1['N_cm'][i - 4] if i >= 4 else ''
        rows.append([str(i), '%.3f' % m, '%.2f' % t1['n_up_cm'][i],
                     '%.2f' % t1['n_down_cm'][i], '%.3f' % t1['n_mean_cm'][i],
                     ('%.3f' % n) if n != '' else ''])
    rows.append(['平均值', '', '', '', 'N̄ =', '%.3f' % t1['N_bar_cm']])
    rows.append(['S_N̄', '', '', '', '', '%.4f' % t1['S_Nbar_cm']])
    T1 = {'t': 'table', 'rows': rows, 'header': 1, 'font': 10.5,
          'widths': [800, 1200, 1500, 1500, 1500, 1800]}

    t2 = calc['t2']
    head = ['项目', '1', '2', '3', '4', '5', '6', '平均值', '修正后']
    row_d = ['直径 d/mm'] + ['%.3f' % x for x in t2['d_mm']] + \
            ['%.3f' % t2['d_bar_mm'], '%.3f' % t2['d_fixed_mm']]
    T2 = {'t': 'table', 'rows': [head, row_d], 'header': 1, 'font': 10.5,
          'widths': [1000, 850, 850, 850, 850, 850, 850, 1100, 1100]}

    t3 = calc['t3']
    head3 = ['物理量', '测量值', '仪器误差', '相对不确定度']
    r_D = ['D（镜面到标尺）/m', '%.4f' % t3['D_m'], '±%.4f' % t3['u_D_m'],
           '%.2f%%' % (t3['u_D_m'] / t3['D_m'] * 100)]
    r_L = ['L（钢丝原长）/m', '%.4f' % t3['L_m'], '±%.4f' % t3['u_L_m'],
           '%.3f%%' % (t3['u_L_m'] / t3['L_m'] * 100)]
    r_K = ['K（光杠杆臂长）/m', '%.4f' % t3['K_m'], '±%.4f' % t3['u_K_m'],
           '%.2f%%' % (t3['u_K_m'] / t3['K_m'] * 100)]
    r_g = ['g（南京地区）/(m·s⁻²)', '%.3f' % t3['g'], '—', '—']
    T3 = {'t': 'table', 'rows': [head3, r_D, r_L, r_K, r_g], 'header': 1, 'font': 10.5,
          'widths': [2400, 1800, 1800, 2300]}
    return T1, T2, T3


def explain(calc, exp):
    r = calc['result']
    t1, t2 = calc['t1'], calc['t2']
    Ns = t1['N_cm']
    lines = [
        '（1）逐差法求每 4 kg 的平均读数变化。八次读数分成前后两组，按 '
        'N_i = n_{i+4} − n_i 求得 N₁~N₄ = %s cm，故 N̄ = %.3f cm，'
        '标准偏差 S = %.4f cm，N̄ 的标准偏差 S_N̄ = %.4f cm。'
        % ('、'.join('%.3f' % x for x in Ns), t1['N_bar_cm'], t1['S_N_cm'], t1['S_Nbar_cm']),
        '（2）求每 4 kg 对应的拉力：F = mg = %.3f × %.3f = %.2f N。'
        % (4.0, calc['t3']['g'], r['F_N']),
        '（3）直径取 6 次测量的平均值并作零点修正：d̄ = %.3f mm，零点读数 %.3f mm，'
        '故 d = %.3f mm。' % (t2['d_bar_mm'], t2['zero_mm'], t2['d_fixed_mm']),
        '（4）代入主公式求杨氏模量：Y = 8FLD/(πd²KN̄)，其中 N̄ = %.4f×10⁻² m，'
        '得 Y = %.4f×10¹¹ Pa = %s Pa。'
        % (r['N_bar_m'] * 1e2, r['Y_Pa'] / 1e11, sci(r['Y_Pa'])),
        '（5）不确定度按相对不确定度合成：直径是平方项（2u_d/d = %.2f%%）、K 为 %.2f%%、'
        'D 为 %.2f%%、L 为 %.3f%%、F 为 %.2f%%、N̄ 为 %.2f%%，合成得 u(Y)/Y = %.2f%%，'
        '即 u(Y) = %.3f×10¹¹ Pa。'
        % (r['components']['d'] * 100, r['components']['K'] * 100, r['components']['D'] * 100,
           r['components']['L'] * 100, r['components']['F'] * 100, r['components']['N'] * 100,
           r['rel_u'] * 100, r['u_Y_Pa'] / 1e11),
        '（6）结果表示：Y = (%.2f ± %.2f)×10¹¹ Pa。与钢丝的公认值 2.0×10¹¹ Pa 相比，'
        '相对误差为 %+.2f%%，在 %.1f 倍不确定度以内，结果合理。'
        % (r['Y_Pa'] / 1e11, r['u_Y_Pa'] / 1e11, r['rel_err_pct'],
           abs(r['rel_err_pct']) / 100 / r['rel_u']),
        '（7）作图法对照：以 F 为横轴、N 为纵轴作图，得直线斜率 '
        'dN/dF = %.3f×10⁻² m·N⁻¹；由 ΔL = KN/(2D) 换算出 ΔL–F 斜率 M = %.4f×10⁻⁵ m·N⁻¹，'
        '再由 Y = 4L/(πd²M) 得 Y = %.3f×10¹¹ Pa，与逐差法相差 %.2f%%。'
        % (r['plot_slope']['slope'], (calc['t3']['K_m'] / (2 * calc['t3']['D_m'])
                                     * r['plot_slope']['slope']) * 1e5,
           r['Y_plot_Pa'] / 1e11, abs(r['Y_plot_Pa'] - r['Y_Pa']) / r['Y_Pa'] * 100),
        '（8）本实验的光杠杆放大倍数 2D/K = 2 × %.3f/%.4f = %.0f 倍，'
        '正是它把 10⁻³ m 量级的微小伸长放大到标尺上可读的厘米量级。'
        % (calc['t3']['D_m'], calc['t3']['K_m'], r['magnification']),
    ]
    return lines


def build(exp, calc, md):
    B = []
    synth = (calc.get('provenance') or {}).get('source') == 'synthetic'

    # 目的
    B.append({'t': 'sect', 'name': '实验目的', 'pct': '10%'})
    for i, s in enumerate(exp.get('objectives', []), 1):
        B.append({'t': 'para', 'text': '%d. %s' % (i, s)})

    # 仪器
    B.append({'t': 'sect', 'name': '实验仪器', 'pct': ''})
    for line in md.get('仪器', []):
        B.append({'t': 'para', 'text': line})

    # 原理
    B.append({'t': 'sect', 'name': '实验原理', 'pct': '10%',
              'note': '(可以拷贝网上文字，最好在理解基础上有所删减，不需完全拷贝。'
                      '需要有实验相关重要的公式及图形。建议手动输入公式，不能粘贴公式图片。)'})
    for key in ('原理1', '原理2', '原理3', '原理4'):
        for line in md.get(key, []):
            B.append({'t': 'para', 'text': line})

    # 步骤
    B.append({'t': 'sect', 'name': '实验内容与步骤', 'pct': '10%',
              'note': '(实验内容及主要操作步骤,可能会因实验仪器的更换有所改变和增减，'
                      '与教材中不同。根据实际操作完成此部分内容)'})
    for line in md.get('步骤', []):
        B.append({'t': 'para', 'text': line})

    # 原始数据
    B.append({'t': 'sect', 'name': '有教师签字的原始数据记录照片（请竖排粘贴）', 'pct': '10%'})
    if synth:
        B.append({'t': 'note', 'text': '（本报告使用示例数据：没有原始数据记录页照片，'
                                       '正式使用时此处粘贴有教师签字的照片。）'})
    else:
        B.append({'t': 'note', 'text': '（此处粘贴原始数据记录页照片）'})

    # 数据处理
    B.append({'t': 'sect', 'name': '数据处理及结果', 'pct': '20%',
              'note': '  (此处的表格要与原始数据记录页的表格一致；表格中的数据要与原始数据记录页中的数据一致；'
                      '表格后处理数据,要有主要的处理过程；要求用作图法处理的可以插入画好图的坐标纸,'
                      '推荐电脑作图；处理的中间结果应多保留1-2位，最终结果表示应符合有效数字规则和'
                      '不确定度位数要求；计算中要特别注意单位的换算和书写。)'})
    for line in md.get('数据说明', []):
        B.append({'t': 'para', 'text': line})

    T1, T2, T3 = tables(calc)
    B.append({'t': 'caption', 'text': '表1 加减砝码时光杠杆镜内标尺像的读数变化值 N', 'bold': True})
    B.append(T1)
    B.append({'t': 'caption', 'text': '表2 钢丝直径 d 数据表（千分尺零点读数 %.3f mm）'
                                      % calc['t2']['zero_mm'], 'bold': True})
    B.append(T2)
    B.append({'t': 'caption', 'text': '表3 各单次测量量', 'bold': True})
    B.append(T3)
    for line in explain(calc, exp):
        B.append({'t': 'para', 'text': line})

    # 体会
    B.append({'t': 'sect', 'name': '分析及体会', 'pct': '20%',
              'note': '（以“我”为主语，描述本次实验的感受。可以说实验中的意外、'
                      '对实验的理解、对课程的建议等，不计空格字符数统计不小于300字）'})
    for line in md.get('体会', []):
        B.append({'t': 'para', 'text': line})

    # 思考题
    B.append({'t': 'heading', 'text': '【思考题】', 'center': False})
    for line in md.get('思考题', []):
        bold = bool(line[:2].strip().rstrip('.').isdigit()) and '（答）' not in line
        B.append({'t': 'para', 'text': line, 'bold': bold, 'indent': not bold})

    # 超星截图位（有截图就贴进去，没有就留提示）
    B.append({'t': 'sect', 'name': '超星平台本实验在线练习得分截图（请竖排粘贴）', 'pct': '5%'})
    B.append({'t': 'shot', 'path': exp.get('_shot'), 'width_cm': 8.2, 'row_h': 3200})
    return B
