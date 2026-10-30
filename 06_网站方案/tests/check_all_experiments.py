# -*- coding: utf-8 -*-
"""每个实验跑一遍：桩数据 -> normalize -> calc -> IR -> docx。

用法：
  python check_all_experiments.py            # 跑所有已登记的实验
  python check_all_experiments.py linear     # 只跑一个（可写多个 id）
不启 HTTP，直接调模块；产出的 docx 落在 07_流水线\\projects\\_p0test\\<id>.docx。
"""
import os
import sys
import traceback

sys.stdout.reconfigure(encoding='utf-8')
W = os.environ.get('DSH_WORKSPACE', r'C:\Users\lidey\Desktop\实验报告制作沙盒')
PIPE = os.path.join(W, '07_流水线')
sys.path.insert(0, PIPE)

import bridge          # noqa: E402  (只为了取 mock_result)
import core            # noqa: E402
import ir              # noqa: E402
import render_docx     # noqa: E402

OUT = os.path.join(PIPE, 'projects', '_p0test')
os.makedirs(OUT, exist_ok=True)

want = [a for a in sys.argv[1:] if not a.startswith('-')]
ids = want or [os.path.splitext(f)[0] for f in sorted(os.listdir(os.path.join(PIPE, 'experiments')))
               if f.endswith('.json')]

ok_all = True
for eid in ids:
    try:
        ed = core.exp_def(eid)
        mock = bridge.mock_result(ed)
        tables = mock.get('tables') or {}
        if not tables:
            raise RuntimeError('没有桩数据（mock_%s.py 缺 tables）' % eid)
        tables = core.normalize_input(ed, tables)
        calc = core.calc_fn(ed)(ed, dict(tables, tables=tables,
                                         provenance={'source': 'mock'}))
        md_path = os.path.join(W, ed['content'])
        if not os.path.exists(md_path):
            md_path = os.path.join(PIPE, ed['content'].replace('07_流水线\\', '').replace('07_流水线/', ''))
        blocks = ir.build(ed, calc, md_path)
        out = os.path.join(OUT, eid + '.docx')
        render_docx.render(blocks, out, ed.get('name'), footer=ed.get('footer') or ed.get('name'))
        r = calc.get('result') or {}
        kpi = []
        for k in ed.get('kpi') or []:
            v = r.get(k['key'])
            if v is None:
                kpi.append('%s=缺失' % k['key'])
            else:
                x = v * k.get('scale', 1)
                kpi.append('%s=%.*f' % (k['key'], k.get('digits', 3), x))
        print('[OK] %-10s blocks=%3d docx=%7.1f KB  %s'
              % (eid, len(blocks), os.path.getsize(out) / 1024.0, ' '.join(kpi)))
    except Exception as e:
        ok_all = False
        print('[FAIL] %-10s %s: %s' % (eid, type(e).__name__, e))
        traceback.print_exc(limit=3)

print('全部通过' if ok_all else '有失败')
sys.exit(0 if ok_all else 1)
