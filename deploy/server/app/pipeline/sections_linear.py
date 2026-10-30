# -*- coding: utf-8 -*-
"""固体线膨胀系数报告的 block 组装（只管「摆什么」，不管「长什么样」）。

渲染细节全部在 render_docx.py；这里只决定顺序、表格内容与计算说明的文字。
"""


def num(v, digits=1):
    return ('%.*f' % (digits, v)).replace('-', '−')


def e5(v, digits=2):
    """把 2.26e-5 这种量按 ×10⁻⁵ 显示。"""
    return '%.*f×10⁻⁵' % (digits, v * 1e5)


def tables(calc):
    t1 = calc['t1']
    head = ['次数'] + [str(i) for i in range(1, t1['n'] + 1)]
    rows = [head]
    rows.append(['设定温度/℃'] + [num(v) for v in t1['set_C']])
    rows.append(['温度 t_i/℃'] + [num(v) for v in t1['t_C']])
    rows.append(['千分表读数 l_i/μm'] + [num(v) for v in t1['l_um']])
    rows.append(['Δt_i = t_i − t₁/℃'] + ['—'] + [num(v) for v in t1['dt_C'][1:]])
    rows.append(['ΔL_i = l_i − l₁/μm'] + ['—'] + [num(v) for v in t1['dL_um'][1:]])
    T1 = {'t': 'table', 'rows': rows, 'header': 1, 'font': 10.5,
          'widths': [1500, 1133, 1133, 1133, 1133, 1134, 1134]}

    t2 = calc['t2']
    r = calc['result']
    comp = r['components']
    head2 = ['物理量', '测量值', '仪器误差限', '相对不确定度']
    rows2 = [head2,
             ['金属棒原长 L₁/mm', num(t2['L1_mm'], 1), '±%s' % num(t2['u_L1_mm'], 1),
              '%s%%' % num(comp['L'] * 100, 2)],
             ['千分表分度值/mm', num(t2['div_mm'], 3), '示值 ±%s' % num(t2['u_l_mm'], 3), '—'],
             ['温控仪分辨力/℃', num(t2['t_div_C'], 1), '±%s' % num(t2['u_t_C'], 1), '—'],
             ['最大温差 Δt/℃', num(r['dt_max'], 1), '±%s' % num(r['u_dt_C'], 2),
              '%s%%' % num(comp['dt'] * 100, 2)],
             ['最大伸长量 ΔL/μm', num(r['dL_max'], 1), '±%s' % num(r['u_dl_um'], 1),
              '%s%%' % num(comp['dL'] * 100, 2)]]
    T2 = {'t': 'table', 'rows': rows2, 'header': 1, 'font': 10.5,
          'widths': [2400, 1800, 1700, 2400]}
    return T1, T2


def explain(calc, exp):
    r = calc['result']
    comp = r['components']
    lines = [
        '（1）先算各次相对第一次的变化：以第一次的 Δt = ΔL = 0 为基准，'
        'Δt_i = t_i − t₁、ΔL_i = l_i − l₁，得到从 0 到 %s ℃ 的 %d 个温差，'
        '对应的伸长量从 0 增到 %s μm。'
        % (num(r['dt_max'], 1), calc['t1']['n'], num(r['dL_max'], 1)),
        '（2）以 Δt 为横轴、ΔL 为纵轴描点，连同原点一起作最小二乘直线拟合，'
        '得斜率 K = %s μm/℃，截距 b = %s μm，相关系数 r = %s，'
        '残差标准差 %s μm。截距不为零说明千分表零点在升温过程中有轻微漂移，'
        '但它只占最大伸长量的 %s，对斜率的影响可以忽略。'
        % (num(r['K'], 2), num(r['b_um'], 2), num(r['r'], 4), num(r['s_resid_um'], 2),
           '%.1f%%' % (abs(r['b_um']) / r['dL_max'] * 100)),
        '（3）由 α = K/L₁ 求线膨胀系数：K = %s×10⁻³ mm/℃，L₁ = %s mm，'
        '故 α = %s ℃⁻¹ = %s ℃⁻¹。'
        % (num(r['K'], 2), num(calc['t2']['L1_mm'], 1), e5(r['alpha'], 5),
           '%.3f×10⁻⁵' % (r['alpha'] * 1e5)),
        '（4）不确定度按相对不确定度合成：斜率的 A 类分量 u(K)/K = %s%%（由拟合残差与'
        'Δt 的散布算出），千分表示值误差带来的 B 类分量 %s%%，温度分辨力带来的 B 类分量 %s%%，'
        '原长本身的 B 类分量 %s%%，合成得 u(α)/α = %s%%，即 u(α) = %s×10⁻⁵ ℃⁻¹。'
        % (num(comp['K'] * 100, 2), num(comp['dL'] * 100, 2), num(comp['dt'] * 100, 2),
           num(comp['L'] * 100, 2), num(r['rel_u'] * 100, 2), num(r['u_alpha'] * 1e5, 2)),
        '（5）结果表示：α = (%s ± %s)×10⁻⁵ ℃⁻¹。'
        '与铝的公认值 2.3×10⁻⁵ ℃⁻¹ 相比，相对误差为 %s%%，在 %s 倍不确定度以内。'
        % (num(r['alpha'] * 1e5, 2), num(r['u_alpha'] * 1e5, 2),
           num(r['rel_err_pct'], 2), num(r['n_sigma'], 1)),
        '（6）两点法对照：只用首末两点，α′ = (l₆ − l₁)/[L₁(t₆ − t₁)] = %s ℃⁻¹，'
        '与拟合值相差 %.1f%%。两种算法的差别集中反映中间几个点的散布，'
        '也说明作图法比两点法更能看出数据是否线性。'
        % (e5(r['alpha_end'], 3), abs(r['alpha_end'] - r['alpha']) / r['alpha'] * 100),
        '（7）线性检验：r² = %s，最大残差与相邻两次的增量相比都很小，'
        '说明在 %s ℃ 的测温区间内 ΔL 与 Δt 确实成线性关系，'
        '常温下忽略 βt² 及更高阶项的近似在本实验的精度内成立。'
        % (num(r['r2'], 5), num(r['dt_max'], 1)),
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

    T1, T2 = tables(calc)
    B.append({'t': 'caption', 'text': '表1 温度与千分表读数记录表', 'bold': True})
    B.append(T1)
    B.append({'t': 'caption', 'text': '表2 单次测量量与主要不确定度来源', 'bold': True})
    B.append(T2)
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

    # 超星截图位
    B.append({'t': 'sect', 'name': '超星平台本实验在线练习得分截图（请竖排粘贴）', 'pct': '5%'})
    B.append({'t': 'shot', 'path': exp.get('_shot'), 'width_cm': 8.2, 'row_h': 3200})
    return B
