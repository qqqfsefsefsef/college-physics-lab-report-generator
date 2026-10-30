# -*- coding: utf-8 -*-
"""用分光计测量三棱镜的折射率（实验 21）报告的 block 组装。

和 sections_young / sections_tungsten 同一套接口：只决定「摆什么」，
长什么样交给 render_docx.py，正文交给 07_流水线\\content\\prism.md。
"""

import math

DEG = math.pi / 180.0


# ----------------------------------------------------------------- 格式化
def num(v, digits=3):
    """保留 digits 位小数，负号统一成 U+2212。"""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return '—'
    return ('%.*f' % (digits, v)).replace('-', '−')


def dm(v, dec=0):
    """十进制度 → '175°40′'（dec=1 时保留到 0.1′，如 '119°58.5′'）。"""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return '—'
    q = 10 ** dec
    total = math.floor(abs(v) * 60.0 * q + 0.5) / q      # 以「分」为单位
    d = int(total // 60)
    m = total - 60.0 * d
    if dec:
        s = '%0*.*f' % (3 + dec, dec, m)                 # '58.5' / '01.0'
    else:
        s = '%02d' % int(m + 0.5)
    return '%d°%s′' % (d, s)


def dms(v, dec=0):
    """十进制度 → '60°01′10″'（秒保留 dec 位）。"""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return '—'
    q = 10 ** dec
    total = math.floor(abs(v) * 3600.0 * q + 0.5) / q
    d = int(total // 3600)
    rest = total - 3600.0 * d
    mi = int(rest // 60)
    sec = rest - 60.0 * mi
    if dec:
        return '%d°%02d′%0*.*f″' % (d, mi, 3 + dec, dec, sec)
    return '%d°%02d′%02d″' % (d, mi, int(sec + 0.5))


def _pct(v, digits=3):
    return ('%.*f' % (digits, v)).replace('-', '−') + '%'


# ----------------------------------------------------------------- 三张表
def tables(calc):
    """表1 顶角 8 列、表2 最小偏向角 6 列、表3 结果 4 列，宽度均合计 8300 twips。"""
    t1, t2, r = calc['t1'], calc['t2'], calc['result']

    # ---- 表1：顶角 A（每两行一对，AB、AC） ----
    rows1 = [['测量次数', '棱镜反射面', '左游标读数', '右游标读数',
              '偏转角\n（左）', '偏转角\n（右）', '无偏心差\n角度', '顶角 A']]
    for row in t1['rows']:
        k = str(row['n'])
        rows1.append([k, 'AB', dm(row['L_ab']), dm(row['R_ab']), '', '', '', ''])
        rows1.append([k, 'AC', dm(row['L_ac']), dm(row['R_ac']),
                      dm(row['phi_L'], 1), dm(row['phi_R'], 1),
                      dm(row['phi'], 1), dm(row['A'], 1)])
    rows1.append(['平均', '', '', '', '', '', '', dm(t1['A_bar'], 1)])
    T1 = {'t': 'table', 'rows': rows1, 'header': 1, 'font': 9.0,
          'widths': [800, 900, 1300, 1300, 1100, 1100, 1050, 750],
          'bold_col0': True, 'row_h': 360}

    # ---- 表2：最小偏向角 δ0（每两行一对，左、右游标） ----
    rows2 = [['测量次数', '读数的位置', '汞绿线的位置', '缝像线的位置',
              'δ0', '无偏心差\nδ0']]
    for row in t2['rows']:
        rows2.append([str(row['n']), row['pos'], dm(row['green']), dm(row['slit']),
                      dm(row['d0'], 1),
                      dm(row['d0_pair'], 1) if row['pos'] != '左' else ''])
    rows2.append(['平均', '', '', '', '', dm(t2['d0_bar'], 1)])
    T2 = {'t': 'table', 'rows': rows2, 'header': 1, 'font': 9.0,
          'widths': [900, 1200, 1700, 1700, 1000, 1800],
          'bold_col0': True, 'row_h': 360}

    # ---- 表3：结果与不确定度 ----
    rel_A = r['u_A_deg'] / r['A_deg'] * 100.0
    rel_d0 = r['u_delta0_deg'] / r['delta0_deg'] * 100.0
    rows3 = [
        ['待测量', '数值', '不确定度', '相对不确定度'],
        ['顶角 A', dm(r['A_deg'], 1), '%d″' % round(r['u_A_deg'] * 3600), _pct(rel_A)],
        ['最小偏向角 δ0', dm(r['delta0_deg'], 1), '%d″' % round(r['u_delta0_deg'] * 3600),
         _pct(rel_d0)],
        ['折射率 n（汞绿线 546.1 nm）', num(r['n'], 4), num(r['u_n'], 4),
         _pct(r['rel_u_n'] * 100.0)],
    ]
    T3 = {'t': 'table', 'rows': rows3, 'header': 1, 'font': 10.0,
          'widths': [2200, 1900, 1900, 2300],
          'bold_col0': True, 'row_h': 380}
    return T1, T2, T3


# ----------------------------------------------------------------- 数据处理正文
def explain(calc, exp):
    t1, t2, r = calc['t1'], calc['t2'], calc['result']
    acc = r.get('accepted_n', 1.5187)
    A, d0 = r['A_deg'], r['delta0_deg']
    h = (A + d0) / 2.0
    lines = []

    if t1['rows']:
        a = t1['rows'][0]
        lines.append(
            '（1）顶角的读数是这样处理的：第 1 次测量时 AB 面对准望远镜，左、右游标依次读 %s、%s；'
            '转到 AC 面读 %s、%s。左游标转过 %s；右游标先读 %s、后读 %s，中间跨过了 0°，'
            '要按 (360° + %s) − %s 计算，得 %s。两侧相差 %s，这正是两个游标之间的偏心差，'
            '取平均后 φ = %s，于是 A = 180° − φ = %s。'
            % (dm(a['L_ab']), dm(a['R_ab']), dm(a['L_ac']), dm(a['R_ac']),
               dm(a['phi_L'], 1), dm(a['R_ab']), dm(a['R_ac']),
               dm(a['R_ac']), dm(a['R_ab']), dm(a['phi_R'], 1),
               dm(abs(a['phi_L'] - a['phi_R']), 1),
               dm(a['phi'], 1), dm(a['A'], 1)))

    A_list = t1.get('A_list') or []
    if len(A_list) >= 3:
        lines.append(
            '（2）三次顶角依次为 %s、%s、%s，平均 %s = %s°。A 类标准差 S(A) = %s°，'
            '平均值的标准差 S(A)/√3 = %s°；B 类按角游标的分度值取 Δ仪 = 1′、按均匀分布，'
            '得 %s°。两类合成 u(A) = %s° = %d″。'
            % (dm(A_list[0], 1), dm(A_list[1], 1), dm(A_list[2], 1), dms(A),
               num(A, 4), num(t1['S_A'], 4), num(t1['S_Abar'], 4),
               num(t1['u_B'], 4), num(r['u_A_deg'], 4), round(r['u_A_deg'] * 3600)))

    d0_list = t2.get('d0_list') or []
    if d0_list:
        lines.append(
            '（3）最小偏向角：每次把望远镜先对准汞绿线、再对准平行光管的缝像，'
            '同一侧游标的两个读数相减，两侧各得一个 δ0。三次测量的左右平均值分别是 %s；'
            '每侧都必须用同一侧游标的两个读数相减，不能拿 289° 附近的左游标去减 70° 附近的右游标。'
            '取平均得 δ0 = %s，δ0 的 A 类平均标准差 %s°，B 类 %s°，合成 u(δ0) = %s° = %d″。'
            % ('、'.join(dm(g['d0'], 1) for g in t2.get('groups', [])),
               dm(d0, 1), num(t2['S_d0bar'], 4), num(t1['u_B'], 4),
               num(r['u_delta0_deg'], 4), round(r['u_delta0_deg'] * 3600)))

    lines.append(
        '（4）把 A 与 δ0 代入折射率公式：n = sin[(A + δ0)/2] / sin(A/2) = '
        'sin %s° / sin %s° = %s / %s = %s。可见分子、分母都接近 0.5—0.76 这个量级，'
        '所以角度的相对误差会被原样带进折射率。'
        % (num(h, 4), num(A / 2.0, 4), num(math.sin(h * DEG), 6),
           num(math.sin(A * DEG / 2.0), 6), num(r['n'], 4)))

    lines.append(
        '（5）不确定度按 u(n)/n = √{[c(A)·u(A)]² + [c(δ)·u(δ0)]²} 传递，'
        '其中 c(A) = ½[cot %s° − cot %s°]·π/180 = %s×10⁻³ /°，'
        'c(δ) = ½cot %s°·π/180 = %s×10⁻³ /°。代入 u(A) = %s°、u(δ0) = %s°，'
        '得 u(n)/n = %s，u(n) = %s。两项大致各占一半，瓶颈是 1′ 的读数分度。'
        % (num(h, 4), num(A / 2.0, 4), num(r['c_A'] * 1e3, 2),
           num(h, 4), num(r['c_delta'] * 1e3, 2),
           num(r['u_A_deg'], 4), num(r['u_delta0_deg'], 4),
           num(r['rel_u_n'] * 100, 3) + '%', num(r['u_n'], 4)))

    lines.append(
        '（6）结果写作 n = %s ± %s（对汞绿线 546.1 nm）。与 K9 冕牌玻璃的 %s 相比，'
        '相对误差 %s，相当于 %.1f 倍不确定度，属于正常的符合；按有效数字规则也可写成 n = %.3f。'
        % (num(r['n'], 4), num(r['u_n'], 4), num(acc, 4),
           ('%+.2f%%' % r['rel_err_pct']).replace('-', '−'),
           r['ratio_u'], r['n']))

    lines.append(
        '（7）单位与易错处：分光计的读数以度、分记，计算前要统一化成十进制度（1′ = 1/60°）；'
        '游标过 0° 时若不加上 360°，φ 会少算一整圈，顶角会直接算成负值；'
        '最小偏向角的两次读数必须取自同一侧游标，否则两个 180° 的固定差会混进 δ0 里。')
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
    B.append({'t': 'caption', 'text': '表1 测量三棱镜的顶角 A', 'bold': True})
    B.append(T1)
    B.append({'t': 'note', 'text': '注：表中两个游标的读数按度、分记；「偏转角」是同一游标在两个反射面'
                                  '位置上的读数差，过 0° 时已按加 360° 处理；顶角 A = 180° − 无偏心差角度。'})
    B.append({'t': 'caption', 'text': '表2 测量三棱镜的最小偏向角 δ0', 'bold': True})
    B.append(T2)
    B.append({'t': 'note', 'text': '注：δ0 由同一侧游标的「汞绿线位置」与「缝像线位置」相减得到，'
                                  '左右两侧取平均即为该次的无偏心差角度。'})
    B.append({'t': 'caption', 'text': '表3 测量结果与不确定度', 'bold': True})
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
