# -*- coding: utf-8 -*-
"""收尾：① 把 _p0test 下 11 份 docx 复制成中文名到 05_成品_报告\\网页流水线版\\；
② 在 07_流水线\\README.md 末尾追加「11 套接入状态」一节（含实测 KPI）；③ 打印清单。"""
import glob
import io
import json
import os
import shutil

W = r'C:\Users\lidey\Desktop\实验报告制作沙盒'
PIPE = os.path.join(W, '07_流水线')
EX = os.path.join(PIPE, 'experiments')
SRC = os.path.join(PIPE, 'projects', '_p0test')
DST = os.path.join(W, '05_成品_报告', '网页流水线版')

os.makedirs(DST, exist_ok=True)

rows = []
for p in sorted(glob.glob(os.path.join(EX, '*.json'))):
    ed = json.loads(io.open(p, encoding='utf-8').read())
    eid, name = ed['id'], ed['name']
    src = os.path.join(SRC, eid + '.docx')
    if not os.path.exists(src):
        rows.append((eid, name, None, '还没生成'))
        continue
    dst = os.path.join(DST, name + '.docx')
    shutil.copyfile(src, dst)
    rows.append((eid, name, os.path.getsize(dst), ed.get('no') or ''))

print('复制到 %s' % DST)
for eid, name, size, no in rows:
    print('  %-10s %-22s %s' % (eid, no, ('%9d B' % size) if size else '（缺）'))

# ---- README 追加状态节
md = os.path.join(PIPE, 'README.md')
txt = io.open(md, encoding='utf-8').read()
mark = '## 十一、11 套实验接入状态'
if mark not in txt:
    lines = [mark, '',
             '| id | 讲稿 | 报告名 | 结果（示例数据，`check_all_experiments.py`） |',
             '|---|---|---|---|',
             '| photo | 实验 47 | 光电效应的研究 | h = 6.750×10⁻³⁴ J·s，误差 +1.88%，u = 0.906 |',
             '| tungsten | 实验 53 | 钨的逸出功测定 | eφ = 4.385 eV，误差 −3.40%，u = 0.111 eV |',
             '| young | 实验 24 | 用静态拉伸法测金属丝的杨氏弹性模量 | Y = 2.017×10¹¹ Pa，u/Y = 2.84% |',
             '| linear | — | 固体线膨胀系数的测定 | α = 2.261×10⁻⁵ ℃⁻¹，误差 −1.69% |',
             '| tension | 实验 26 | 液体表面张力系数测定 | α = 74.50 mN/m，误差 +2.85% |',
             '| malus | 实验 8 | 验证马吕斯定律 | k = 0.979，r = 0.9998，偏差 0.81% |',
             '| prism | 实验 21 | 用分光计测量三棱镜的折射率 | n = 1.5190，误差 +0.02% |',
             '| light | 实验 49 | 光速测定 | c = 3.053×10⁸ m/s，误差 +1.84% |',
             '| michelson | 实验 42 | 迈克耳孙干涉仪 | λ = 631.3 nm，误差 −0.23% |',
             '| hfield | 实验 31 | 用霍尔效应测磁场 | B₀ = 2.250 mT，叠加偏差 0.71% |',
             '| hall | 实验 30 | 霍尔效应及其应用 | n = 1.921×10²¹ m⁻³，R_H = 32.49 |',
             '',
             '新增一个实验 = 只写 5 个文件（见 `EXPERIMENT_SPEC.md`），`core.py`/`bridge.py`/`ir.py`/`render_docx.py` 都不用动。',
             '',
             '## 十二、部署（让别人也能用）',
             '',
             '见 `06_网站方案\\部署指南.md`：三种方案（局域网 ¥0 / Cloudflare Tunnel ¥0 / 云服务器 ¥30–60 月），',
             '以及上线前必须补的三处（bridge 地址可配置、访问口令、projects 自动清理）。',
             '其中「bridge 地址可配置」与「访问口令 `BRIDGE_TOKEN`」已经做完：',
             '页面右上角「连接设置」可改地址与口令，`python bridge.py --host 0.0.0.0` 可对局域网开放。',
             '']
    txt = txt.rstrip('\n') + '\n\n' + '\n'.join(lines)
    io.open(md, 'w', encoding='utf-8', newline='\n').write(txt)
    print('\n[OK] README 追加状态节')
else:
    print('\n[SKIP] README 已有状态节')
