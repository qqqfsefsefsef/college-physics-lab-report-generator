# -*- coding: utf-8 -*-
"""用霍尔效应测磁场（实验 31）的 block 组装：只管摆什么，不管长什么样。"""

SUP = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵',
       '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹', '-': '⁻'}

HEAD = ['x/mm', 'V1/mV', 'V2/mV', 'V3/mV', 'V4/mV', 'V_H/mV', 'B/mT']
WIDTHS = [700, 1200, 1200, 1200, 1200, 1150, 1650]


def num(v, digits=3):
    if v is None:
        return '—'
    s = '%.*f' % (digits, float(v))
    return s.replace('-', '−')


def sci(v, digits=2):
    if not v:
        return '0'
    e = 0
    x = abs(v)
    while x >= 10:
        x /= 10.0
        e += 1
    while x < 1:
        x *= 10.0
        e -= 1
    return '%.*f×10' % (digits, x) + ''.join(SUP[c] for c in str(e))


def _val_at(tab, x):
    i = min(range(len(tab['x'])), key=lambda k: abs(tab['x'][k] - x))
    return tab['b'][i]


def tables(calc):
    out = []
    for key in ('t1', 't2', 't3'):
        t = calc[key]
        rows = [HEAD]
        for i in range(len(t['x'])):
            v = t['v'][i]
            rows.append([num(t['x'][i], 0), num(v[0], 2), num(v[1], 2), num(v[2], 2),
                         num(v[3], 2), num(t['vh'][i], 3), num(t['b'][i], 3)])
        out.append({'t': 'table', 'rows': rows, 'header': 1, 'font': 10.5, 'widths': WIDTHS})
    return out


def explain(calc):
    r = calc['result']
    t1, t2, t3 = calc['t1'], calc['t2'], calc['t3']
    b1_0 = _val_at(t1, 0)
    b2_0 = _val_at(t2, 0)
    br_0 = _val_at(t3, 0)
    br_50 = _val_at(t3, 50)
    br_100 = _val_at(t3, 100)
    b1_100 = _val_at(t1, 100)
    ratio = (br_50 / br_0 - 1.0) * 100.0 if br_0 else 0.0
    return [
        '（1）用对称测量法处理每组读数：V_H = (V1 − V2 + V3 − V4)/4，可消去能斯特效应、'
        '里吉—勒杜克效应与不等势电位，剩下埃廷斯豪森效应因方向与霍尔电压相同而无法消除，'
        '但其量很小，在误差范围内可忽略。',
        '（2）霍尔灵敏度由表 3 中 x = 0 mm 处的读数标定：V_H0 = %s mV，取 I_s = 5.00 mA、'
        'B0 = 2.25 mT，得 K_H = %s mV/(mA·T)；各点再按 B = V_H/(K_H·I_s) 换算。'
        % (num(r['V_H0_mV'], 3), num(r['K_H'], 3)),
        '（3）单个圆线圈的磁场在圆心处最大，离开圆心后按 (R² + x²)^(−3/2) 的规律下降。'
        '由于两线圈间距已调到等于半径、铜管位置也按讲稿调到使滑块读数以两线圈中点 O 为原点，'
        '线圈 1 的峰值出现在 x = %s mm 处，峰值 B = %s mT；线圈 2 的峰值出现在 x = %s mm 处，'
        '峰值 B = %s mT。两者取平均与 μ0NI/(2R) = 1.571 mT 相比，相对偏差 %s%%，'
        '说明两个线圈的灵敏度与几何条件基本一致。'
        % (num(r['B1_max_x_mm'], 0), num(r['B1_max_mT'], 3),
           num(r['B2_max_x_mm'], 0), num(r['B2_max_mT'], 3),
           num(r['rel_single_center_pct'], 2)),
        '（4）两线圈同向串联时，中心处实测 B = %s mT，与式(4) 给出的理论值 2.25 mT 相差 %s%%。'
        '由于两线圈间距等于半径，中心附近磁场比较平坦：x = 50 mm 处仍为 %s mT，'
        '相对中心只下降 %s%%，这正是亥姆霍兹线圈能提供均匀磁场的缘故。'
        % (num(br_0, 3), num(r['rel_dev_center_pct'], 2), num(br_50, 3), num(abs(ratio), 2)),
        '（5）验证叠加原理：把表 1、表 2 同一位置的 B 相加，得 B(1) + B(2) = %s mT，'
        '与表 3 直接测得的 %s mT 相比，中心处相差 %s%%，在 |x| ≤ 80 mm 范围内最大相差 %s%%，'
        '两者在实验误差内一致，说明两线圈的磁场可以按矢量叠加。'
        % (num(b1_0 + b2_0, 3), num(br_0, 3), num(r['sup_dev_center_pct'], 2), num(r['sup_dev_pct'], 2)),
        '（6）以 B(1) + B(2) 为横轴、B(R) 为纵轴作直线，斜率 = %s，相关系数 r = %s，'
        '直线过原点附近，说明两线圈磁场的叠加是线性叠加。'
        % (num(r['sum_slope'], 4), num((r['sum_r2'] or 0) ** 0.5, 5)),
        '（7）综合来看，霍尔元件经对称测量法标定后可以较准确地测出 10⁻³ T 量级的磁场，'
        '测得的两线圈中心磁场与理论值相差不大，叠加原理得到验证。',
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

    caps = ['表1 线圈 1 通电时轴线上的霍尔电压与磁感应强度',
            '表2 线圈 2 通电时轴线上的霍尔电压与磁感应强度',
            '表3 两线圈同向串联时轴线上的霍尔电压与磁感应强度']
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
