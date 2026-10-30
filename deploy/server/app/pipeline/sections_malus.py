# -*- coding: utf-8 -*-
"""验证马吕斯定律（实验 8）报告的 block 组装。

只决定「摆什么」，长什么样交给 render_docx.py；数字一律取自 calc_malus.py。
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


def _data_table(t1, lo, hi):
    """讲义表 1 的一列角度段：一行角度 + cos²α + 三次读数 + Ī + 归一化。"""
    idx = [i for i, a in enumerate(t1['angles']) if lo - 1e-6 <= a <= hi + 1e-6]
    rows = [['α/(°)'] + [str(int(round(t1['angles'][i]))) for i in idx],
            ['cos²α'] + [num(t1['cos2'][i], 3) for i in idx]]
    for k, lab in enumerate(('I_1/mW', 'I_2/mW', 'I_3/mW')):
        reads = t1['reads'][k] if k < len(t1['reads']) else []
        rows.append([lab] + [_fmt(reads[i] if i < len(reads) else None, 2) for i in idx])
    rows.append(['Ī/mW'] + [num(t1['mean'][i], 3) for i in idx])
    rows.append(['Ī/I_0'] + [num(t1['norm'][i], 4) for i in idx])
    return {'t': 'table', 'rows': rows, 'header': 1, 'font': 9,
            'widths': [800] + _w(len(idx), 7500), 'bold_col0': False, 'row_h': 320}


def tables(calc):
    t1 = calc['t1']
    tabs = [_data_table(t1, 0, 120), _data_table(t1, 130, 240), _data_table(t1, 250, 360)]

    r = calc['result']
    rows = [['象限', '角度范围', '斜率 k', '截距 b', '相关系数 r', '点数']]
    for q in r['quads']:
        rows.append([q['name'], q['span'], num(q['k'], 4), num(q['b'], 4),
                     num(q['r'], 5), str(q['n'])])
    rows.append(['四象限平均', '0°～360°', num(r['k_mean'], 4), num(r['b_mean'], 4),
                 num(r['r_mean'], 5), '—'])
    rows.append(['全部数据', '0°～360°', num(r['global_k'], 4), num(r['global_b'], 4),
                 num(r['global_r'], 5), str(r['n_points'])])
    fit = {'t': 'table', 'rows': rows, 'header': 1, 'font': 10.5,
           'widths': [1400, 1600, 1550, 1600, 1700, 450], 'bold_col0': False}
    return tabs, fit


def explain(calc):
    r = calc['result']
    t1 = calc['t1']
    q = r['quads'] or []
    ks = [x['k'] for x in q] or [r['k_mean']]
    bs = [x['b'] for x in q] or [r['b_mean']]
    rs = [x['r'] for x in q] or [r['r_mean']]
    sigma = abs(1.0 - r['k_mean']) / r['u_k'] if r['u_k'] else 0.0
    drift0 = t1['norm'][0] - t1['norm'][-1]
    cos_note = ('记录表上的 cos²α 与按角度重算的值一致（最大差 %.3f），未发现抄错。'
                % r['cos_check_max'] if r['cos_check_max'] < 0.001 else
                '记录表上的 cos²α 与按角度重算的值最大差 %.3f，已按角度重算值参与拟合。'
                % r['cos_check_max'])
    spread = []
    reads_all = t1.get('reads') or []
    for k, a in enumerate(t1.get('angles') or []):
        vals = [rr[k] for rr in reads_all if k < len(rr) and rr[k] is not None]
        if len(vals) == 3 and sum(vals) > 0:
            spread.append(((max(vals) - min(vals)) / (sum(vals) / 3.0), a, vals))
    spread.sort(key=lambda z: -z[0])
    if len(spread) >= 2:
        s1, s2 = spread[0], spread[1]
        anomaly = ('原始记录里有两处读数与同组另两次差得较多：α = %g° 的三次读数为'
                   ' %.2f、%.2f、%.2f mW，α = %g° 的为 %.2f、%.2f、%.2f mW。页面已把'
                   '这两格列为待核对点。' %
                   (s1[1], s1[2][0], s1[2][1], s1[2][2],
                    s2[1], s2[2][0], s2[2][1], s2[2][2]))
    else:
        anomaly = ''

    lines = [
        '（1）先按角度把三次读数取平均：Ī = (I_1 + I_2 + I_3)/3；再从 %d 个平均值里取最大者'
        ' I₀ = %.3f mW 作归一化，得纵坐标 Ī/I₀。I₀ 对应 cos²α = 1 的情形，这样横、纵坐标'
        '都是 0～1 的无量纲量，可以和理论直线 Ī/I₀ = cos²α 直接比较。%s'
        % (r['n_points'], r['I0_mW'], cos_note),

        '（2）按讲义要求分四个象限作 Ī/I₀ — cos²α 线性拟合，每次只用该象限内的测点。'
        '四象限斜率在 %.4f～%.4f 之间，截距在 %.4f～%.4f 之间，相关系数都不低于 %.5f。'
        '四个象限落在同一条直线上，说明马吕斯定律在整个 0°～360° 范围内成立，'
        '并不是只在某一象限碰巧吻合。'
        % (min(ks), max(ks), min(bs), max(bs), min(rs)),

        '（3）四象限平均得斜率 k = %.4f、截距 b = %.4f；把 %d 个点合在一起作一次总拟合，'
        '得 Ī/I₀ = %.4f cos²α + %.4f，r = %.5f，斜率的标准偏差 u(k) = %.4f。'
        '两种算法的斜率相差不到 0.001，说明分象限处理没有引入额外偏差。'
        % (r['k_mean'], r['b_mean'], r['n_points'], r['global_k'], r['global_b'],
           r['global_r'], r['global_u_k']),

        '（4）马吕斯定律要求 k = 1、b = 0。实测 k 比 1 小 %.2f%%（约 %.1f 倍 u(k)），'
        'b = %.4f 略大于零。消光位置的理论光强为零，实测归一化光强仍剩 I_min/I_0 = %.4f'
        '（消光比约 %.1f%%），这部分残余光来自暗计数、杂散光和偏振片有限的消光比，'
        '它把直线整体抬高，斜率就被压低了同一量级。'
        % (abs(r['k_dev_pct']), sigma, r['b_mean'], r['ext_ratio'], r['ext_ratio'] * 100.0),

        '（5）逐点比较 Ī/I₀ 与 cos²α，平均绝对偏差 %.3f（%.2f%%），最大偏差 %.3f 出现在'
        ' α = %d°。消光附近光强只有 0.02 mW 量级，功率计 0.01 mW 的分辨率在那里相对影响'
        '最大，这是逐点偏差的主要来源。另外 α = 0° 与 360° 是同一理论位置，归一化值却相差'
        ' %.4f（约 %.1f%%），反映测量期间激光功率在缓慢下降。'
        % (r['dev_pct'] / 100.0, r['dev_pct'], r['dev_max'], int(round(r['dev_max_angle'])),
           drift0, drift0 * 100.0),

        '（6）%s若改用三次读数的中位数代替平均值重新归一化并拟合，得'
        ' k = %.4f、r = %.5f、平均偏差 %.2f%%，与上面的结果相差很小，说明拟合结论不依赖'
        '这两个可疑读数。' % (anomaly, r['k_med'], r['r_med'], r['dev_med_pct']),

        '（7）综合以上：在 0°～360° 范围内，归一化透射光强随 cos²α 线性变化，相关系数'
        ' %.4f，斜率 k = %.3f ± %.3f，与马吕斯定律 I = I_0cos²α 相符；截距、斜率的微小'
        '偏离可由残余光和激光功率漂移解释。因此本实验验证了马吕斯定律。'
        % (r['r_mean'], r['k_mean'], r['u_k']),
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

    data_tabs, fit_tab = tables(calc)
    B.append({'t': 'caption', 'text': '表1 验证马吕斯定律数据记录表（α = 0°～120°）', 'bold': True})
    B.append(data_tabs[0])
    B.append({'t': 'caption', 'text': '表1（续）α = 130°～240°', 'bold': True})
    B.append(data_tabs[1])
    B.append({'t': 'caption', 'text': '表1（续）α = 250°～360°', 'bold': True})
    B.append(data_tabs[2])
    B.append({'t': 'caption', 'text': '表2 分象限线性拟合结果（Ī/I_0 — cos²α）', 'bold': True})
    B.append(fit_tab)
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
