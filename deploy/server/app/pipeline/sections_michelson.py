# -*- coding: utf-8 -*-
"""迈克耳孙干涉仪（实验 42）报告的 block 组装。

接口与 sections_young / sections_tungsten 相同：只决定摆什么，
版式交给 render_docx.py，正文交给 07_流水线\\content\\michelson.md。
"""

import math


def num(v, digits=3):
    """保留 digits 位小数，负号统一成 U+2212。"""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return '—'
    return ('%.*f' % (digits, v)).replace('-', '−')


def _pct(v, digits=2):
    return ('%.*f' % (digits, v)).replace('-', '−') + '%'


def _signed_pct(v, digits=2):
    return ('%+.*f' % (digits, v)).replace('-', '−') + '%'


# ----------------------------------------------------------------- 三张表
def tables(calc):
    """表1 7 列、表2 5 列、表3 4 列，宽度均合计 8300 twips。"""
    t1, t2, r = calc['t1'], calc['t2'], calc['result']

    # ---- 表1：N 与动镜位置 → 波长 ----
    rows1 = [['测量次数', 'N\n（个）', 'd1/mm', 'd2/mm', 'Δd=|d2−d1|\n(mm)',
              'λ=2Δd/N\n(nm)', 'λ平均\n(nm)']]
    for row in t1['rows']:
        rows1.append([str(row['n']), str(int(round(row['N']))),
                      num(row['d1'], 5), num(row['d2'], 5),
                      num(row['dd'], 5), num(row['lambda_nm'], 1), ''])
    rows1.append(['平均', '', '', '',
                  num(r['dd_mean_mm'], 5), '', num(r['lambda_nm'], 1)])
    T1 = {'t': 'table', 'rows': rows1, 'header': 1, 'font': 9.0,
          'widths': [1000, 900, 1400, 1400, 1300, 1300, 1000],
          'bold_col0': True, 'row_h': 360}

    # ---- 表2：可见度两次为零之间的镜移量 ----
    rows2 = [['测量次数', 'd1/mm', 'd2/mm', 'd=|d2−d1|\n(mm)', 'd平均\n(mm)']]
    for row in t2['rows']:
        rows2.append([str(row['n']), num(row['d1'], 5), num(row['d2'], 5),
                      num(row['d'], 5), ''])
    rows2.append(['平均', '', '', '', num(r['d_bar_mm'], 5)])
    T2 = {'t': 'table', 'rows': rows2, 'header': 1, 'font': 10.0,
          'widths': [1000, 1900, 1900, 1600, 1900],
          'bold_col0': True, 'row_h': 380}

    # ---- 表3：结果与不确定度 ----
    rows3 = [
        ['待测量', '数值', '不确定度', '相对不确定度'],
        ['氦—氖激光的波长 λ', '%s nm' % num(r['lambda_nm'], 1),
         '%s nm' % num(r['u_lambda_nm'], 1), _pct(r['rel_u_lam'] * 100.0)],
        ['钠光的相干长度（镜移量 d̄）', '%s mm' % num(r['d_bar_mm'], 4),
         '%s mm' % num(r['u_d_mm'], 4), _pct(r['rel_u_d'] * 100.0)],
        ['理论相干长度 λ₀²/Δλ', '%s mm' % num(r['Lc_theory_mm'], 4), '—', '—'],
    ]
    T3 = {'t': 'table', 'rows': rows3, 'header': 1, 'font': 10.0,
          'widths': [2200, 1900, 1900, 2300],
          'bold_col0': True, 'row_h': 400}
    return T1, T2, T3


# ----------------------------------------------------------------- 数据处理正文
def explain(calc, exp):
    t1, t2, r = calc['t1'], calc['t2'], calc['result']
    acc = r.get('accepted_nm', 632.8)
    lines = []

    rows = t1['rows']
    if rows:
        a = rows[0]
        lines.append(
            '（1）以第 1 次为例，动镜先后停在 d1 = %s mm 和 d2 = %s mm，'
            '两读数之差 Δd = |d2 − d1| = %s mm；数过的条纹数 N = %d，'
            '于是 λ = 2Δd/N = 2×%s/%d mm = %s nm。三次测量依次得 %s nm，'
            '平均 λ = %s nm。'
            % (num(a['d1'], 5), num(a['d2'], 5), num(a['dd'], 5),
               int(round(a['N'])), num(a['dd'], 5), int(round(a['N'])),
               num(a['lambda_nm'], 1),
               '、'.join(num(x, 1) for x in r['lambda_list']),
               num(r['lambda_nm'], 1)))

    lines.append(
        '（2）为什么每数过 200 条才记一次读数：N 越大，条纹计数的偶然误差被摊得越薄，'
        'Δd 的读数误差也被 2/N 压得越小；但 N 太大时人容易数漏、手轮也容易转过界，'
        '200 条是两者之间的折中。整个计数过程微调手轮只能朝一个方向转，中途倒回会引入'
        '丝杠的空程差，读到的 d2 就不再对应真实的镜移量。')

    lines.append(
        '（3）不确定度这样估计：三次测量的分散给出 A 类，标准差 S(λ) = %s nm，'
        '平均值的标准差 S/√3 = %s nm；B 类有两项，一是动镜读数的误差限取 %s mm，'
        '经 λ = 2Δd/N 放大后折合 %s nm，二是条纹计数按 ±0.5 条估计，折合 %s nm。'
        '两类合成得 u(λ) = √(%s² + %s²) = %s nm，相对不确定度 %s。'
        '可见主要的不确定度来自数条纹本身，而不是手轮的读数。'
        % (num(r['S_lambda_nm'], 2), num(r['S_lambdabar_nm'], 2),
           '%s×10⁻⁵' % num(2.0, 0), num(r['u_B_dd_nm'], 2),
           num(r['u_B_N_nm'], 2),
           num(r['S_lambdabar_nm'], 2), num(r['u_B_lambda_nm'], 2),
           num(r['u_lambda_nm'], 2), _pct(r['rel_u_lam'] * 100.0, 2)))

    lines.append(
        '（4）结果写作 λ = %s ± %s nm。与氦—氖激光的公认波长 %s nm 相比，相对误差 %s，'
        '只有不确定度的 %.1f 倍，说明测量值与公认值在误差范围内一致。'
        % (num(r['lambda_nm'], 1), num(r['u_lambda_nm'], 1), num(acc, 1),
           _signed_pct(r['rel_err_pct'], 2), r['ratio_u']))

    if r.get('cell_lambda_bar_nm') is not None and not (
            isinstance(r['cell_lambda_bar_nm'], float) and math.isnan(r['cell_lambda_bar_nm'])):
        lines.append(
            '（5）原始记录里有一处要改：第 2 次的 λ 一栏写的是 %s nm，可同一行的 Δd 与 N 重算'
            '应是 %s nm，末两位抄颠倒了；平均值一栏照这三个数算成 %s nm，也就跟着偏了。'
            '按三次的 Δd 重算得 %s nm，与公认值只差 %s，若照抄记录页的 %s 反而会算成 %s。'
            % (num(r['cell_lambda_nm'][1], 1), num(r['lambda_list'][1], 1),
               num(r['cell_lambda_bar_nm'], 1), num(r['lambda_nm'], 1),
               _signed_pct(r['rel_err_pct'], 2),
               num(r['cell_lambda_bar_nm'], 1),
               _signed_pct(r['cell_lambda_bar_nm'] / acc * 100.0 - 100.0, 2)))

    lines.append(
        '（6）钠光那一组测的是可见度的周期性变化：三次的镜移量 d 依次为 %s mm，'
        '平均 d̄ = %s mm，与按 ΔL = λ₀²/Δλ 算出的理论相干长度 %s mm 相差 %s。'
        '讲稿只说「两次读数的差即为相干长度」，没写光程差是镜移量的两倍，也没写这个间隔'
        '为什么等于 λ₀²/Δλ；本报告把它说明白：相邻两次可见度为零之间镜移 λ₀²/(2Δλ)，'
        '而记录的是「零可见度再出现两次」的间隔，正好等于 λ₀²/Δλ。'
        % ('、'.join(num(x, 5) for x in t2['d_list']), num(r['d_bar_mm'], 5),
           num(r['Lc_theory_mm'], 4), _signed_pct(r['rel_Lc_pct'], 2)))

    lines.append(
        '（7）单位与易错处：动镜位置的读数以 mm 记，Δd 只有 10⁻² mm 量级，'
        '书写时要保留足够的位数；波长用 nm，讲稿表 1 用 Å，1 Å = 0.1 nm，'
        '忘记乘十倍或除十倍是最常见的差错。条纹数 N 是无量纲的整数，'
        '数错一条对 λ 的影响就相当于 N 的千分之五，比手轮读数的影响大得多。')
    return lines


# ----------------------------------------------------------------- 组装
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

    T1, T2, T3 = tables(calc)
    r = calc['result']
    B.append({'t': 'caption', 'text': '表1 测量氦—氖激光的波长', 'bold': True})
    B.append(T1)
    B.append({'t': 'note', 'text': '注：Δd 与 λ 由 d1、d2 和 N 重算得到，不照抄记录页上的中间值；'
                                  '每数过 N = 200 个圆环记一次动镜位置。'})
    B.append({'t': 'caption', 'text': '表2 测量钠光的相干长度', 'bold': True})
    B.append(T2)
    B.append({'t': 'note', 'text': '注：d1、d2 是视场中心可见度两次趋于零时动镜的位置读数，'
                                  'd 为两者之差，即一个「可见度周期」内动镜的移动量。'})
    B.append({'t': 'caption', 'text': '表3 测量结果与不确定度', 'bold': True})
    B.append(T3)
    B.append({'t': 'note', 'text': '注：理论相干长度按 λ₀²/Δλ 计算，钠双线取 λ₀ = %s nm、'
                                  'Δλ = %s nm；波长与不确定度按有效数字规则修约后再比较。'
                                  % (num(r['lam0_na_nm'], 1), num(r['dl_nm'], 3))})
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
