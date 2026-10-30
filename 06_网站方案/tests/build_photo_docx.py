"""离线把光电效应的 IR 跑出来并渲染成 docx（不需要桥、不需要 key）。

用法：python tests\build_photo_docx.py
产出：07_流水线\projects\photo-demo\out\光电效应的研究.docx
"""
import json
import os
import shutil
import sys

W = r'C:\Users\lidey\Desktop\实验报告制作沙盒'
HERE = os.path.join(W, '07_流水线')
sys.path.insert(0, HERE)

import bridge    # noqa: E402  只为拿桩数据
import core      # noqa: E402
import ir        # noqa: E402
import render_docx  # noqa: E402

ed = json.load(open(os.path.join(HERE, 'experiments', 'photo.json'), encoding='utf-8'))
mock = bridge.mock_result(ed)
tables = mock['tables']
tables['provenance'] = {'source': 'mock',
                        'note': '识别桩数据（界面演练用），不是真实测量；正式生成时来自用户照片'}
calc = core.calc_photo(ed, tables)

proj = os.path.join(HERE, 'projects', 'photo-demo')
os.makedirs(os.path.join(proj, 'out'), exist_ok=True)
json.dump(tables, open(os.path.join(proj, 'data.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
json.dump(calc, open(os.path.join(proj, 'calc.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

md_path = os.path.join(W, ed['content'])
blocks = ir.build(ed, calc, md_path)
out_docx = os.path.join(proj, 'out', '光电效应的研究.docx')
render_docx.render(blocks, out_docx, ed['name'])

r = calc['result']
print('ok  blocks=%d  docx=%.1f KB' % (len(blocks), os.path.getsize(out_docx) / 1024.0))
print('h = %.4e J·s   rel = %+.2f%%   u(h) = %.2e   r = %.5f'
      % (r['h'], r['rel_err_pct'], r['u_h'], r['r']))
