# -*- coding: utf-8 -*-
"""液体表面张力系数报告的 block 组装（只管「摆什么」，不管「长什么样」）。

渲染细节全部在 render_docx.py；这里只决定顺序、表格内容与计算说明的文字。
"""


def num(v, digits=1):
    return ('%.*f' % (digits, v)).replace('-', '−')


def e3(v, digits=2):
    """把 0.0745 这种量按 ×10⁻³ 显示。"""
    return '%.*f×10⁻³' % (digits, v * 1e3)


def e4(v, digits=3):
    """把 8.16e-4 这种量按 ×10⁻⁴ 显示。"""
    return '%.*f×10⁻⁴' % (digits, v * 1e4)


def _mean(v):
    return sum(v) / float(len(v))


def tables(calc):
    t1 = calc['t1']
    head = ['砝码质量 /10⁻⁶kg', '增重读数 U_i /mV', '减重读数 U_i /mV',
            '平均值 /mV', 'U_i − U_i−4 /mV', 'K /(N·mV⁻¹)']
    rows = [head]
    for i in range(t1['n']):
        dv = t1['dU_mV'][i]
        kv = t1['K'][i]
        rows.append([num(t1['mass_mg'][i], 2), num(t1['u_up'][i], 2),
                     num(t1['u_down'][i], 2), num(t1['u_mean'][i], 2),
                     '—' if dv is None else num(dv, 2),
                     '—' if kv is None else e4(kv)])
    rows.append(['平均值', '—', '—', '—', '—', e4(t1['K_mean'])])
    T1 = {'t': 'table', 'rows': rows, 'header': 1, 'font': 10.0,
          'widths': [1900, 1100, 1100, 1100, 1400, 1700]}

    t2 = calc['t2']
    head2 = ['测量次数', '拉脱时最大读数 U₁′ /mV', '吊环读数 U₂′ /mV',
             '表面张力对应读数 ΔU_i /mV']
    rows2 = [head2]
    for i in range(t2['n']):
        u1 = t2['u1_mV'][i]
        u2 = t2['u2_mV'][i]
        rows2.append([str(i + 1),
                      '—' if u1 is None else num(u1, 2),
                      '—' if u2 is None else num(u2, 2),
                      num(t2['dU_mV'][i], 2)])
    rows2.append(['平均值', '—', '—', num(t2['dU_mean'], 2)])
    rows2.append(['水温（室温）/℃',
                  '—' if t2['water_C'] is None else num(t2['water_C'], 1), '', ''])
    T2 = {'t': 'table', 'rows': rows2, 'header': 1, 'font': 10.0,
          'widths': [1700, 2200, 1600, 2800]}

    t3 = calc['t3']
    head3 = ['测量次数', '1', '2', '3', '4', '5', '平均值']
    rows3 = [head3,
             ['内径 D₁ /mm'] + [num(v, 2) for v in t3['D1_list']]
             + [num(t3['D1_mm'] + t3['zero_mm'], 2)],
             ['外径 D₂ /mm'] + [num(v, 2) for v in t3['D2_list']]
             + [num(t3['D2_mm'] + t3['zero_mm'], 2)],
             ['游标卡尺零点读数 /mm', num(t3['zero_mm'], 2), '', '', '', '', '']]
    T3 = {'t': 'table', 'rows': rows3, 'header': 1, 'font': 10.5,
          'widths': [1900, 1100, 1100, 1100, 1100, 1000, 1000]}
    return T1, T2, T3


def explain(calc, exp):
    r = calc['result']
    comp = r['components']
    t1 = calc['t1']
    t2 = calc['t2']
    t3 = calc['t3']
    lines = [
        '（1）定标逐差：把 0～%s×10⁻⁶ kg 的 %d 组读数按相隔 4 个台阶相减，'
        'ΔU = U_i − U_i−4 的平均值为 %s mV；每个台阶对应 4×10⁻³ kg 的砝码，'
        '由此得 K = 4mg/ΔU，四次结果分别为 %s、%s、%s、%s N·mV⁻¹，'
        '平均值 K = %s N·mV⁻¹。'
        % (num(t1['mass_mg'][-1], 0), int(t1['n']), num(t1['dU_cal_mean'], 2),
           e4(r['K_list'][0]), e4(r['K_list'][1]), e4(r['K_list'][2]),
           e4(r['K_list'][3]), e4(r['K'])),
        '（2）拉脱读数：五次 ΔU_i = U₁′ − U₂′ 的平均值 Ū = %s mV。'
        '其中第 %d 次的 U₁′ 比其余四次高出一截，使 ΔU 的散布变大：'
        'A 类分量 u(Ū)/Ū = %s%%，B 类只由电压表分辨力贡献、约 0.01%%，'
        '合成得 u(Ū)/Ū = %s%%。'
        % (num(t2['dU_mean'], 2), r['excl_index'], num(
            (t2['u_dU'] / t2['dU_mean']) * 100, 2), num(comp['U'] * 100, 2)),
        '（3）由 α = K(Ū₁′ − Ū₂′)/[π(D₁ + D₂)] 求表面张力系数：'
        'K·Ū = %s×10⁻³ N，D₁ + D₂ = %s mm = %s m，'
        '故 α = %s N·m⁻¹ = %s N·m⁻¹。'
        % (num(r['K'] * r['dU_mean'] * 1e3, 2), num(t3['Dsum_mm'], 3),
           num(t3['Dsum_mm'] * 1e-3, 5), num(r['alpha'], 5), e3(r['alpha'], 3)),
        '（4）不确定度按相对分量合成：定标系数 u(K)/K = %s%%（A 类 %s%%、B 类 %s%%），'
        '拉脱读数 u(Ū)/Ū = %s%%，吊环直径和 u(D₁+D₂)/(D₁+D₂) = %s%%；'
        '合成得 u(α)/α = %s%%，即 u(α) = %s N·m⁻¹。'
        % (num(comp['K'] * 100, 2), num(t1['uA_K_rel'] * 100, 2),
           num(t1['uB_K_rel'] * 100, 3), num(comp['U'] * 100, 2),
           num(comp['D'] * 100, 2), num(r['rel_u'] * 100, 2), e3(r['u_alpha'], 3)),
        '（5）结果表示：α = (%s ± %s)×10⁻³ N·m⁻¹。'
        '查附录一，%s ℃ 时水的表面张力系数为 %s×10⁻³ N·m⁻¹，'
        '相对误差为 %s%%，约为 %s 倍不确定度。'
        % (num(r['alpha'] * 1e3, 2), num(r['u_alpha'] * 1e3, 2),
           num(r['water_C'], 1), num(r['accepted'] * 1e3, 2),
           num(r['rel_err_pct'], 2), num(r['n_sigma'], 1)),
        '（6）可疑读数核查：若把第 %d 次的拉脱读数当作峰值抢读而剔除，'
        '其余四次的 Ū = %s mV，α = %s×10⁻³ N·m⁻¹，与附录值只差 %s%%，'
        '落在 1 倍不确定度以内。这说明 %s%% 的偏差主要来自那一次读数，'
        '而不是定标或吊环尺寸。'
        % (r['excl_index'], num(r['dU_excl'], 2), num(r['alpha_excl'] * 1e3, 2),
           num(r['rel_err_excl'], 2), num(r['rel_err_pct'], 2)),
        '（7）吊环尺寸的影响：表 3 内径第三次的 %s mm 比其余四次大约 0.40 mm，'
        '疑为游标卡尺只卡在倒角上；若改用内径中位数 %s mm，'
        'α 只变为 %s×10⁻³ N·m⁻¹（变化约 %s%%）。因为 D₁、D₂ 只以和的形式出现在'
        '分母上，且卡尺精度远高于拉脱读数的相对误差，所以直径不是主要误差来源。'
        % (num(t3['D1_list'][2], 2) if len(t3['D1_list']) > 2 else '—',
           num(t3['D1_median_mm'], 2), num(r['alpha_Dfix'] * 1e3, 2),
           num(abs(r['alpha_Dfix'] - r['alpha']) / r['alpha'] * 100, 2)),
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
    B.append({'t': 'caption', 'text': '表1 力敏传感器的转换系数', 'bold': True})
    B.append(T1)
    B.append({'t': 'caption', 'text': '表2 用拉脱法求拉力对应的读数', 'bold': True})
    B.append(T2)
    B.append({'t': 'caption', 'text': '表3 吊环的内、外直径', 'bold': True})
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

    # 超星截图位
    B.append({'t': 'sect', 'name': '超星平台本实验在线练习得分截图（请竖排粘贴）', 'pct': '5%'})
    B.append({'t': 'shot', 'path': exp.get('_shot'), 'width_cm': 8.2, 'row_h': 3200})
    return B
