# -*- coding: utf-8 -*-
"""钨的逸出功（实验 53）报告的 block 组装。

和 sections_photo / sections_young 同一套接口：只决定「摆什么」，
长什么样交给 render_docx.py，正文交给 04_生成过程_脚本图表\content_tungsten.md。
"""

import os

GEN = os.environ.get('PIPE_GEN',
                     r'C:\Users\lidey\Desktop\实验报告制作沙盒\04_生成过程_脚本图表')
FIGT = os.path.join(GEN, 'figures_tungsten')


def num(v, digits=3):
    """保留 digits 位，负号统一成 U+2212。"""
    return ('%.*f' % (digits, v)).replace('-', '−')


def _fig(path, w, cap):
    return {'t': 'figure', 'path': path, 'width_cm': w, 'caption': cap}


def _fixed(v, digits=2):
    """'%.2f' 但整数不带小数点（表 1 的 I_a / μA 用）。"""
    s = '%.*f' % (digits, v)
    return s[:-3] if s.endswith('.00') else s


def tables(calc):
    """三张表：表1 9x9、表2 9x9、表3 4x9，宽度合计 8300 twips。"""
    t1, t2, t3 = calc['table1'], calc['table2'], calc['table3']

    # ---- 表1：I_a(μA) 随 U_a、I_f ----
    rows1 = [['U_a / V\nI_a / μA\nI_f / A'] + [str(int(u)) for u in t1['u_a_V']]]
    for i, f in enumerate(t1['i_f_A']):
        rows1.append(['%.3f' % f] + [_fixed(v, 1) for v in t1['i_a_uA'][i]])
    T1 = {'t': 'table', 'rows': rows1, 'header': 1, 'font': 10.0,
          'widths': [1500] + [850] * 8, 'bold_col0': True, 'row_h': 360}

    # ---- 表2：lg I_a 随 sqrt(U_a)、T ----
    rows2 = [['√U_a\nlg I_a\nT / 10³K'] + [num(v, 1) for v in t2['sqrt_u_a']]]
    for i, T in enumerate(t2['T_1000K']):
        rows2.append(['%.2f' % T] + [num(v, 2) for v in t2['lg_i_a'][i]])
    extra = t2.get('lg_i_a_row_T216_extra')
    if extra:
        rows2.append(['2.16'] + [num(v, 2) for v in extra])
    T2 = {'t': 'table', 'rows': rows2, 'header': 1, 'font': 10.0,
          'widths': [1500] + [850] * 8, 'bold_col0': True, 'row_h': 360}

    # ---- 表3：lg(I_s/T²) ~ 1/T ----
    rows3 = [
        ['T / 10³K'] + [num(v, 2) for v in t3['T_1000K']],
        ['1/T（10⁻³K⁻¹）'] + [num(v, 2) for v in t3['inv_T_1e3_per_K']],
        ['lg I_s'] + [num(v, 2) for v in t3['lg_i']],
        ['lg(I_s/T²)'] + [num(v, 2) for v in t3['lg_is_over_T2_written']],
    ]
    T3 = {'t': 'table', 'rows': rows3, 'header': 0, 'font': 10.0,
          'widths': [1900] + [800] * 8, 'bold_col0': True, 'row_h': 380}
    return T1, T2, T3


def explain(calc, exp):
    r = calc['result']
    fit = calc['fit']
    k = (calc.get('meta') or {}).get('constants') or {}
    k_k = k.get('k_J_per_K', 1.3806505e-23)
    acc = r.get('accepted_eV', 4.54)
    lines = [
        '（1）里查孙直线法的做法：先在同一灯丝电流（同一温度）下测一组 lg I_a–√U_a，'
        '把直线外推到 √U_a = 0 得到零场电流的对数 lg I_s，于是每个温度对应一个 I_s；'
        '再作 lg(I_s/T²)–1/T 图，斜率里只有逸出功，A 与 S 都落在截距上，这样就把两个'
        '测不准的量绕开了。',
        '（2）对表 3 的八个点作最小二乘拟合，得 lg(I_s/*T*²) = %.3f×(1/T) + %.3f'
        '（1/T 以 10⁻³ K⁻¹ 计），相关系数 r = %.4f，r² = %.4f，说明线性关系很好。'
        % (fit['slope'], fit['intercept'], fit['r'], fit['r2']),
        '（3）横轴用的是 10⁻³ K⁻¹，换回真单位斜率 m′ = %.3f × 10³ = %.4e K⁻¹。'
        % (fit['slope'], r['slope_true_per_K']),
        '（4）由 lg(I_s/*T*²) = lg AS − 0.4343·eφ/(*k*·*T*) 得 eφ = 2.303·*k*·|m′|，'
        '代入 k = %.4f×10⁻²³ J·K⁻¹：eφ = 2.303 × %.4f×10⁻²³ × %.4e = %.3e J，'
        '即 φ = %.3f V，eφ = %.2f eV。'
        % (k_k * 1e23, k_k * 1e23, abs(r['slope_true_per_K']), r['phi_J'],
           r['phi_eV'], r['phi_eV']),
        '（5）与公认值 eφ₀ = %.2f eV 相比，相对误差 E = (%.3f − %.2f)/%.2f = %+.1f%%。'
        % (acc, r['phi_eV'], acc, acc, r['rel_err_pct']),
        '（6）斜率的标准偏差 u(m) = %.3f（以 10⁻³ K⁻¹ 计），传到逸出功上得 '
        'u(eφ) = %.3f eV，所以结果写作 eφ = (%.2f ± %.2f) eV。'
        % (fit['se_slope'], r['u_phi_eV'], r['phi_eV'], r['u_phi_eV']),
        '（7）表 3 第四行按原始记录记的是 lg(I_s/T²)，其中 T 用的是 T/10³ K，'
        '所以整行比真值高出 2lg1000 = 6.000；这只是一个平移，斜率不变，'
        '逸出功的结果不受影响。',
    ]
    if r.get('phi_eV_exact_inv_T'):
        lines.append('（8）作为核对，若改用未经截断的 1/T（0.5319、0.5208 …）重新拟合，'
                     '得到 eφ = %.2f eV，与上面相差不到 2%%，说明取两位小数的影响很小。'
                     % r['phi_eV_exact_inv_T'])
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
    B.append(_fig(os.path.join(GEN, 'fig_w_wiring.png'), 12.6,
                  '图1 实验线路原理示意图'))
    B.append(_fig(os.path.join(GEN, 'fig_w_tcal.png'), 12.6,
                  '图2 阴极温度与灯丝电流的关系'))
    B.append({'t': 'caption', 'text': '附表1 灯丝温度与灯丝电流的关系', 'bold': True})
    T1c, T2c, T3c = tables(calc)
    B.append({'t': 'table', 'header': 1, 'font': 10.0, 'bold_col0': True, 'row_h': 360,
              'widths': [1500] + [971] * 7,
              'rows': [['I_f / A', '0.50', '0.55', '0.60', '0.65', '0.70', '0.75', '0.80'],
                       ['T / 10³K', '1.72', '1.80', '1.88', '1.96', '2.04', '2.12', '2.20']]})

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

    B.append({'t': 'caption', 'text': '表1 不同灯丝电流 I_f 和阳极电压 U_a 对应的阳极电流 I_a 值',
              'bold': True})
    B.append(T1c)
    B.append(_fig(os.path.join(FIGT, 'fig_w1.png'), 14.3,
                  '图3 不同灯丝电流下的阳极电流—阳极电压曲线'))
    B.append({'t': 'caption', 'text': '表2 不同温度 T 和 √U_a 下对应的阳极电流对数值 lg I_a',
              'bold': True})
    B.append(T2c)
    B.append({'t': 'note', 'text': '注：表 2 第 8 行（T = 2.16×10³ K）学生写在表格框线外，'
                                  '按与表 1 第 8 行的对应关系补入行标签；表 3 第 3 行按原始记录'
                                  '只保留两位小数。'})
    B.append(_fig(os.path.join(FIGT, 'fig_w2.png'), 14.3,
                  '图4 各温度下 lg I_a–√U_a 直线外推求 lg I_s'))
    B.append({'t': 'caption', 'text': '表3 lg(I_s/T²)～1/T 数据表', 'bold': True})
    B.append(T3c)
    B.append(_fig(os.path.join(FIGT, 'fig_w3.png'), 14.3,
                  '图5 lg(I_s/T²)–1/T 直线与最小二乘拟合'))
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
