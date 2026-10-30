# -*- coding: utf-8 -*-
"""流水线 CLI（M1，钨的逸出功跑通）

用法：
  python pipeline.py init    --exp tungsten --slug tungsten-2026-10-13 --date 2026-10-13
  python pipeline.py import  --slug ... --from <data_tungsten.json>     # ② 读图结果（本版为导入/手工）
  python pipeline.py review  --slug ...                                  # ③ 闸门：出核对清单
  python pipeline.py confirm --slug ... --all --note "已逐格核对"        #    用户确认
  python pipeline.py calc    --slug ...                                  # ④ 计算（需闸门通过）
  python pipeline.py render  --slug ... --formats docx,html              # ⑥ 渲染
  python pipeline.py status  --slug ...
  python pipeline.py all     --slug ... --from <json> --note "..."

约定：⓪ 格式选择 → meta.formats；⑦ 存档 = 项目目录本身。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

try:                      # GBK 控制台：打不出的字符降级成 '?'，不要把流程打断
    sys.stdout.reconfigure(errors='replace')
    sys.stderr.reconfigure(errors='replace')
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core
from core import Project, exp_def, jload, jsave, now

PY = sys.executable
HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(os.path.dirname(HERE), '04_生成过程_脚本图表')
WORK = os.path.dirname(HERE)


def cmd_init(a):
    p = Project.create(a.exp, a.slug, a.date)
    print('[OK] 项目已建：%s' % p.dir)
    print('  ⓪ 输出格式：%s（可用 --formats 改）' % ','.join(p.meta['formats']))
    print('  ① 素材目录：%s' % p.src)
    return p


def _map_from_datatungsten(raw):
    """把 04 里 data_tungsten.json 的形态转成项目 data.json 的形态。"""
    t1 = raw['table1']
    t2 = raw['table2']
    t3 = raw['table3']
    lg2 = list(t2['lg_i_a'])
    # 第 8 行（T=2.16）在原文件里单独存放，这里合并回去
    if t2.get('lg_i_a_row_T216_extra'):
        lg2 = lg2 + [t2['lg_i_a_row_T216_extra']]
    T = list(t3['T_1000K'])
    if len(T) < len(lg2):
        T = T + [round(920.0 + 1600 * x) / 1000.0 for x in t1['i_f_A'][len(T):]]
    return {
        'tables': {
            't1': {'u_a_V': t1['u_a_V'], 'i_f_A': t1['i_f_A'], 'i_a_uA': t1['i_a_uA']},
            't2': {'sqrt_u_a': t2['sqrt_u_a'], 'T_1000K': T, 'lg_i_a': lg2},
            't3': {'T_1000K': T, 'inv_T_1e3_per_K': t3['inv_T_1e3_per_K'],
                   'lg_i': t3['lg_i'], 'lg_is_over_T2_written': t3['lg_is_over_T2_written']},
        },
        'unconfirmed': [],
        'provenance': {'read': 'import:' + 'data_tungsten.json', 'at': now()},
    }


def _map_young(raw):
    """杨氏模量的导入：样本 JSON 已经是项目形态，只补默认字段。"""
    return {
        'tables': raw['tables'],
        'constants': raw.get('constants', {}),
        'unconfirmed': raw.get('unconfirmed', []),
        'confidence': raw.get('confidence', {}),
        'provenance': raw.get('provenance', {'source': 'manual'}),
    }


def cmd_import(a):
    p = Project(a.slug)
    if not os.path.exists(p.meta_p):
        sys.exit('项目不存在：%s' % p.dir)
    if not a.src:
        sys.exit('请用 --from 指定数据来源（视觉模型输出 / 手工录入 / 既有 data_*.json）')
    raw = jload(a.src)
    if not raw:
        sys.exit('读不到：%s' % a.src)
    if p.meta['exp'] == 'young':
        data = _map_young(raw)
    elif 'table1' in raw:
        data = _map_from_datatungsten(raw)
    else:
        data = raw
    data['exp'] = p.meta['exp']
    p.save_data(data)
    p.stamp('import', src=os.path.basename(a.src))
    tabs = data.get('tables', {})
    shapes = []
    for k in sorted(tabs):
        cols = [v for v in tabs[k].values() if isinstance(v, list)]
        shapes.append('%s(%d×%d)' % (k, len(cols[0]) if cols else 0, len(cols)))
    prov = (data.get('provenance') or {}).get('source', '?')
    print('[OK] 读入 %s  来源=%s' % (' '.join(shapes), prov))
    if prov == 'synthetic':
        print('     ! 这是示例数据（非实测），成品里会标注，不能直接提交')
    return p


def cmd_review(a):
    p = Project(a.slug)
    ed = exp_def(p.meta['exp'])
    findings = core.review(ed, p.data)
    html = core.review_html(p, ed, findings)
    p.stamp('review', findings=len(findings),
            block=sum(1 for f in findings if f['level'] == 'block'))
    print('[OK] 核对清单：%s' % html)
    for f in findings:
        if f['level'] in ('block', 'warn'):
            print('  [%s] %s — %s' % (f['level'], f['where'], f['msg']))
    print('  共 %d 条（block %d / warn %d / info %d）'
          % (len(findings),
             sum(1 for f in findings if f['level'] == 'block'),
             sum(1 for f in findings if f['level'] == 'warn'),
             sum(1 for f in findings if f['level'] == 'info')))
    return p


def cmd_confirm(a):
    p = Project(a.slug)
    m = p.meta
    findings = core.review(exp_def(m['exp']), p.data)
    blocks = [f['id'] for f in findings if f['level'] == 'block']
    accepted = list(a.accept or [])
    left = [b for b in blocks if b not in accepted]
    if not a.all and left:
        sys.exit('还有 %d 条 block 未处理：%s\n（用 --accept id 逐条处理，或 --all 表示全部接受当前值）'
                 % (len(left), ', '.join(left)))
    m['gate'] = {
        'confirmed': True,
        'at': now(),
        'by': a.note or 'user',
        'decisions': ({'accept_all': True} if a.all else {'accepted': accepted}),
        'blocked_before': blocks,
    }
    p.save_meta(m)
    print('[OK] 闸门已通过（%s）' % m['gate']['by'])
    return p


def _result_line(r):
    if 'phi_eV' in r:
        return 'e\u03c6 = %.4f eV\uff0c\u76f8\u5bf9\u8bef\u5dee %+.2f%%\uff0cu = %.4f eV' % (r['phi_eV'], r['rel_err_pct'], r['u_phi_eV'])
    if 'Y_Pa' in r:
        return 'Y = %.4e Pa\uff08%.3f\u00d710\u00b9\u00b9\uff09\uff0cu(Y)/Y = %.2f%%\uff0c\u8bef\u5dee %+.2f%%' % (r['Y_Pa'], r['Y_Pa']/1e11, r['rel_u']*100, r['rel_err_pct'])
    return ', '.join('%s=%s' % (k, ('%.4g' % v)) for k, v in r.items() if isinstance(v, (int, float)))


def cmd_calc(a):
    p = Project(a.slug)
    p.require_gate('计算')
    ed = exp_def(p.meta['exp'])
    fn = getattr(core, 'calc_' + ed['calc'])
    res = fn(ed, p.data)
    res['exp'] = p.meta['exp']
    res['computed_at'] = now()
    jsave(p.calc_p, res)
    r = res['result']
    p.stamp('calc', summary=_result_line(r))
    print('[OK] 计算完成 → %s' % os.path.basename(p.calc_p))
    print('  ' + _result_line(r))
    return p


def acc_str(r):
    return '%.3e J' % r['phi_J']


def cmd_render(a):
    p = Project(a.slug)
    p.require_gate('渲染')
    m = p.meta
    formats = [x.strip() for x in (a.formats or ','.join(m['formats'])).split(',') if x.strip()]
    made = []
    if 'calc.json' not in os.listdir(p.dir):
        sys.exit('还没算：先 python pipeline.py calc --slug %s' % p.slug)

    # ⑦ 存档：把这次用到的图拷进项目，项目才能脱离 04 目录独立重渲
    for f in exp_def(m['exp']).get('figures', []):
        src = f.get('src', '')
        if not src:
            continue
        src = src if os.path.isabs(src) else os.path.join(GEN, src)
        dst = os.path.join(p.figs, os.path.basename(src))
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)

    # 渲染器需要的中间件：把项目数据转成渲染器认识的形状
    ed = exp_def(m['exp'])
    if ed.get('renderer') == 'ir':
        renderer = os.path.join(HERE, 'ir.py')
    else:
        renderer = os.path.join(GEN, 'build_report_%s.py' % ed['render_key'])
    content = a.content or ed.get('content', 'content_tungsten.md')
    if content and not os.path.isabs(content):
        cand = [os.path.join(WORK, content), os.path.join(GEN, content)]
        content = next((c for c in cand if os.path.exists(c)), cand[0])
    docx_out = os.path.join(p.out, '%s.docx' % a.name)

    if 'docx' in formats:
        shot = ed.get('shot') or ''
        if shot and not os.path.isabs(shot):
            shot = os.path.join(WORK, shot)
        env = dict(os.environ)
        env.update({
            'PIPE_GEN': GEN, 'PIPE_DATA': p.calc_p, 'PIPE_MD': content,
            'PIPE_OUT': docx_out,
            'PIPE_BASE': os.path.join(WORK, '03_参考模板_旧报告', '热膨胀系数.docx'),
            'PIPE_SHOT': shot,
        })
        if ed.get('renderer') == 'ir':
            exp_p = os.path.join(HERE, 'experiments', m['exp'] + '.json')
            cmd = [PY, renderer, '--exp', exp_p, '--calc', p.calc_p, '--md', content,
                   '--out', docx_out, '--blocks', os.path.join(p.dir, 'blocks.json'),
                   '--title', m.get('title', '')]
        else:
            cmd = [PY, renderer]
        r = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit('docx 渲染失败：\n' + (r.stderr or r.stdout))
        made.append(docx_out)

    if 'html' in formats and 'docx' in formats:
        conv = os.path.join(GEN, 'docx_to_print_html.py')
        r = subprocess.run([PY, conv, docx_out], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit('html 渲染失败：\n' + (r.stderr or r.stdout))
        made.append(os.path.splitext(docx_out)[0] + '_打印版.html')

    if 'json' in formats:
        dst = os.path.join(p.out, '%s.json' % a.name)
        jsave(dst, {'data': p.data, 'calc': p.calc, 'meta': m})
        made.append(dst)

    m['formats'] = formats
    p.save_meta(m)
    p.stamp('render', formats=formats, files=[os.path.basename(x) for x in made])
    for f in made:
        print('[OK] %s  (%.1f KB)' % (f, os.path.getsize(f) / 1024.0))
    return p


def cmd_status(a):
    p = Project(a.slug)
    m = p.meta
    print('项目 : %s' % p.slug)
    print('实验 : %s · %s' % (m['exp_name'], m['title']))
    print('格式 : %s' % ','.join(m.get('formats', [])))
    print('闸门 : %s' % ('已确认 %s' % m['gate']['at'] if m['gate']['confirmed'] else '未确认'))
    for k in ('import', 'review', 'calc', 'render'):
        s = m.get('steps', {}).get(k)
        print('  %-7s %s' % (k, s['at'] if s else '—'))
    if os.path.exists(p.calc_p):
        r = p.calc.get('result', {})
        print('结果 : %s' % _result_line(r))
    return p


def cmd_all(a):
    p = cmd_init(a) if not os.path.exists(Project(a.slug).meta_p) else Project(a.slug)
    cmd_import(a)
    cmd_review(a)
    cmd_confirm(a)
    cmd_calc(a)
    cmd_render(a)
    cmd_status(a)


def main():
    ap = argparse.ArgumentParser(description='实验报告流水线（M1）')
    sub = ap.add_subparsers(dest='cmd', required=True)

    def common(sp, need_src=False, need_formats=False):
        sp.add_argument('--slug', required=True)
        if need_src:
            sp.add_argument('--from', dest='src', default='')
        if need_formats:
            sp.add_argument('--formats', default='')
            sp.add_argument('--content', default='')
            sp.add_argument('--name', default='报告')

    sp = sub.add_parser('init', help='⓪① 建项目')
    sp.add_argument('--exp', default='tungsten')
    sp.add_argument('--slug', required=True)
    sp.add_argument('--date', default='')
    sp.add_argument('--formats', default='docx,html')
    sp.set_defaults(fn=cmd_init)

    sp = sub.add_parser('import', help='② 读入数据（视觉模型输出 / 手工 / 既有 json）')
    common(sp, need_src=True)
    sp.set_defaults(fn=cmd_import)

    sp = sub.add_parser('review', help='③ 出核对清单')
    common(sp)
    sp.set_defaults(fn=cmd_review)

    sp = sub.add_parser('confirm', help='③ 用户确认（过闸门）')
    common(sp)
    sp.add_argument('--all', action='store_true')
    sp.add_argument('--accept', action='append')
    sp.add_argument('--note', default='')
    sp.set_defaults(fn=cmd_confirm)

    sp = sub.add_parser('calc', help='④ 计算')
    common(sp)
    sp.set_defaults(fn=cmd_calc)

    sp = sub.add_parser('render', help='⑥ 渲染导出')
    common(sp, need_formats=True)
    sp.set_defaults(fn=cmd_render)

    sp = sub.add_parser('status', help='看进度')
    common(sp)
    sp.set_defaults(fn=cmd_status)

    sp = sub.add_parser('all', help='一条龙')
    sp.add_argument('--exp', default='tungsten')
    sp.add_argument('--slug', required=True)
    sp.add_argument('--date', default='')
    sp.add_argument('--formats', default='docx,html')
    sp.add_argument('--from', dest='src', required=True)
    sp.add_argument('--content', default='')
    sp.add_argument('--name', default='报告')
    sp.add_argument('--note', default='')
    sp.add_argument('--accept', action='append')
    sp.set_defaults(fn=cmd_all)

    a = ap.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
