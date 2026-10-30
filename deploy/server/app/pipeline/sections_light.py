# -*- coding: utf-8 -*-
"""光速测定（实验 49）报告的 block 组装。

只决定「摆什么」，长什么样交给 render_docx.py；数字一律取自 calc_light.py。
"""


def num(v, digits=4):
    return ('%.*f' % (digits, v)).replace('-', '−')


def _fmt(v, digits):
    return '—' if v is None else num(v, digits)


def _w(n, total):
    """把 total twips 尽量平均分给 n 列，保证总和严格等于 total。"""
    base = total // n
    ws = [base] * n
    for k in range(total - base * n):
        ws[k] += 1
    return ws


def _t1_table(t1):
    """表 1：等间距法，位置 x0～x4 各列，行为读数、D、r、φ、λ。"""
    n = len(t1['x'])
    rows = [['位置'] + ['x_%d' % i for i in range(n)],
            ['读数/cm'] + [_fmt(v, 2) for v in t1['x']],
            ['D_i/cm'] + [_fmt(v, 2) for v in t1['D']],
            ['r_i/格'] + [_fmt(v, 2) for v in t1['r']],
            ['φᵢ/rad'] + [_fmt(v, 3) for v in t1['phi']]]
    lam = []
    for j in range(n):
        lam.append('—' if j == 0 else num(t1['lam_calc'][j - 1], 3))
    rows.append(['λᵢ/m'] + lam)
    rows.append(['λ̄/m', num(t1['mean'], 3), '', '', '', ''])
    return {'t': 'table', 'rows': rows, 'header': 1, 'font': 9,
            'widths': [1100] + _w(n, 7200), 'bold_col0': False,
            'row_h': 340, 'merges': [(len(rows) - 1, 1, len(rows) - 1, n)]}


def _t2_table(t2):
    """表 2：等相位法，三次测量各列。"""
    n = len(t2['lam_calc'])
    rows = [['测量次数'] + ['第 %d 次' % (j + 1) for j in range(n)],
            ['φᵢ/(°)'] + ['%d' % round(t2['phi_deg'][j]) for j in range(n)],
            ['X_0/cm'] + [_fmt(v, 2) for v in t2['X0']],
            ['X_i/cm'] + [_fmt(v, 2) for v in t2['Xi']],
            ['X_0′/cm'] + [_fmt(v, 2) for v in t2['X0p']],
            ['X̄_0/cm'] + [_fmt(v, 2) for v in t2['Xbar']],
            ['D_i/cm'] + [_fmt(v, 2) for v in t2['D']],
            ['λᵢ/m'] + [num(v, 3) for v in t2['lam_calc']],
            ['λ̄/m', num(t2['mean'], 3)] + [''] * (n - 1)]
    return {'t': 'table', 'rows': rows, 'header': 1, 'font': 9,
            'widths': [1700, 2200, 2200, 2200], 'bold_col0': False,
            'row_h': 340, 'merges': [(len(rows) - 1, 1, len(rows) - 1, n)]}


def tables(calc):
    t1 = calc['t1']
    t2 = calc['t2']
    r = calc['result']
    rows = [['方法', 'λ̄/m', 'c/(10⁸ m·s⁻¹)', '相对误差/%'],
            ['等间距法', num(r['lam1'], 3), num(r['c_1e8'], 3),
             num(r['rel_err_pct'], 2)],
            ['等相位法', num(r['lam2'], 3), num(r['c_2e8'], 3),
             num(r['rel_err_2_pct'], 2)]]
    summary = {'t': 'table', 'rows': rows, 'header': 1, 'font': 10.5,
               'widths': [2000, 1900, 2300, 2100], 'bold_col0': False,
               'row_h': 360}
    return _t1_table(t1), _t2_table(t2), summary


def explain(calc):
    t1, t2, r = calc['t1'], calc['t2'], calc['result']
    lams1 = t1['lam_calc']
    lams2 = t2['lam_calc']
    lines = [
        '（1）表 1 是等间距法的记录。由 φᵢ = 2πr_i/5 把相移格数换成相移量，'
        '再由 λᵢ = 2π·2D_i/φᵢ = 10D_i/r_i 逐点求波长（D 以 m 计）。四个测点得'
        ' λᵢ = %s m，各点之间散布约 %.1f%%，平均 λ̄ = %.4f m。'
        '取 f = %.1f MHz，得 c = λ̄f = %.4f×10⁸ m/s，与公认值 2.998×10⁸ m/s 相比'
        '偏大 %.2f%%。'
        % ('、'.join(num(v, 3) for v in lams1),
           (max(lams1) - min(lams1)) / (sum(lams1) / len(lams1)) * 100.0,
           r['lam1'], r['f_mhz'], r['c_1e8'], r['rel_err_pct']),

        '（2）表 1 第 3 行有一处抄写问题：x_4 = %.2f cm、x_0 = %.2f cm，'
        'D_4 应为 %.2f cm，记录表上却写成 %.2f cm，相差 %.2f cm（页面已把它列为'
        '待核对点）。按记录值算得 λ₄ = %.3f m，明显高于其余各点，'
        '把平均波长抬到 %.4f m。若改用 x_4 − x_0 重算，λ̄ = %.4f m、'
        ' c = %.4f×10⁸ m/s（偏大 %.2f%%），可见这一格笔误是等间距法结果偏大的主要来源。'
        % (t1['x'][-1], t1['x'][0], t1['x'][-1] - t1['x'][0], t1['D'][-1],
           t1['D'][-1] - (t1['x'][-1] - t1['x'][0]), lams1[-1], r['lam1'], r['lam1_fix'],
           r['c1_fix_1e8'], (r['c1_fix_1e8'] * 1e8 - 2.998e8) / 2.998e8 * 100.0),

        '（3）表 2 是等相位法的记录。每次把反射镜移到 72° 相位点，并迅速拉回 0° 复测'
        ' X_0′，取 X̄_0 = (X_0 + X_0′)/2，得 D_i = X_i − X̄_0 = %s cm；'
        '由 λᵢ = 4πD_i/φ（φ = 72° = 1.2566 rad）得 λᵢ = %s m，平均 λ̄ = %.4f m，'
        ' c = %.4f×10⁸ m/s，偏大 %.2f%%。'
        % ('、'.join(num(v, 2) for v in t2['D']),
           '、'.join(num(v, 3) for v in lams2), r['lam2'], r['c_2e8'],
           r['rel_err_2_pct']),

        '（4）表 2 第 3 次测量的 X_0′ = %.2f cm，与同一次的 X_0 = %.2f cm 相差'
        ' %.2f cm，超过了讲义「两次 0° 读数误差不超过 5 mm，否则须重测」的要求，'
        '很可能是把 X_0′ 抄错。该点使 D 偏小、λ₃ 偏低。若用同次的 X_0 代替 X_0′ 重算，'
        ' λ̄ = %.4f m、c = %.4f×10⁸ m/s（偏大 %.2f%%）。页面已把这一格列为待核对点。'
        % (t2['X0p'][-1], t2['X0'][-1], abs(t2['X0p'][-1] - t2['X0'][-1]),
           r['lam2_fix'], r['c2_fix_1e8'],
           (r['c2_fix_1e8'] * 1e8 - 2.998e8) / 2.998e8 * 100.0),

        '（5）两种方法互相独立：等间距法用一段导轨上的多个等间距位置，等相位法用同一'
        '相位点重复三次。实测 c 分别为 %.4f×10⁸ m/s 和 %.4f×10⁸ m/s，分别比公认值大'
        ' %.2f%% 和 %.2f%%，两者相差 %.2f%%。单点散布折合到平均值的不确定度 u(c) 分别为'
        ' %.4f×10⁸ m/s 和 %.4f×10⁸ m/s，远小于与公认值的偏差，说明偏差主要来自'
        '系统误差（示波器时基刻度、一周期格数的标定、导轨读数零点）而不是随机误差；'
        '两种方法给出一致的系统偏移，也支持这一判断。'
        % (r['c_1e8'], r['c_2e8'], r['rel_err_pct'], r['rel_err_2_pct'],
           r['two_method_diff_pct'], r['u_c_1e8'], r['u_c_2e8']),

        '（6）主要误差来源：示波器上相移格数靠人工估读，0.1 大格约合 7.2°，即使用光标'
        '细读到 0.01 大格也还有约 0.7°；一周期究竟占多少大格、时基是否校准，都会按'
        '同一比例影响所有 λᵢ；导轨刻度读数约 0.05 cm，对 30 cm 以上的 D 只有千分之几；'
        '频率计给出的 100 MHz 很准，不构成主要误差；空气折射率 1.0003 使光速比真空值'
        '小 0.03%，可以忽略。把 D 取大一些、多测几个相位点并作线性拟合，可以进一步'
        '压低格数估读的影响。',

        '（7）综合以上：调制波法测得 λ ≈ %.2f～%.2f m，c ≈ %.2f×10⁸ m/s，'
        '与公认值 2.998×10⁸ m/s 的偏差为个位数百分比；两种独立方法结果一致，'
        '说明用相位差测调制波波长、再由 c = λf 求光速的方案是可行的。'
        % (min(r['lam1'], r['lam2']), max(r['lam1'], r['lam2']),
           (r['c_1e8'] + r['c_2e8']) / 2.0),
    ]
    return lines


def build(exp, calc, md):
    B = []
    src = (calc.get('provenance') or {}).get('source')

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
    if src in ('mock', 'synthetic'):
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

    t1_tab, t2_tab, summary = tables(calc)
    B.append({'t': 'caption', 'text': '表1 等间距法数据记录表（f = 100 MHz，一周期 5 大格）',
              'bold': True})
    B.append(t1_tab)
    B.append({'t': 'caption', 'text': '表2 等相位法数据记录表（φ = 72°）', 'bold': True})
    B.append(t2_tab)
    B.append({'t': 'caption', 'text': '表3 两种方法测得的光速对比', 'bold': True})
    B.append(summary)
    for line in explain(calc):
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

    # 超星截图位
    B.append({'t': 'sect', 'name': '超星平台本实验在线练习得分截图（请竖排粘贴）', 'pct': '5%'})
    B.append({'t': 'shot', 'path': exp.get('_shot'), 'width_cm': 8.2, 'row_h': 3200})
    return B
