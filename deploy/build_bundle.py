# -*- coding: utf-8 -*-
"""
把「能跑起来的最小集合」复制到 deploy/server/，这个目录可以整包扔到任何一台 Linux 服务器上。

产物结构（deploy/server/）：
    app/web/prototype_v2.html          前端（单文件）
    app/pipeline/*.py                  引擎：core / ir / render_docx / style / bridge / calc_* / mock_* / sections_*
    app/pipeline/experiments/*.json    11 套实验定义
    app/pipeline/content/*.md          11 套正文
    app/assets/*.png  & figures/ & figures_tungsten/   报告里的插图
    app/assets/template.docx           排版骨架（热膨胀系数.docx，带页眉页脚与样式）
    Dockerfile / Caddyfile / docker-compose.yml / .env.example / install.sh

用法：
    python deploy/build_bundle.py           # 重新组装（幂等，可重复跑）
"""
import io
import json
import os
import shutil
import sys

W = os.environ.get('DSH_WORKSPACE', r'C:\Users\lidey\Desktop\实验报告制作沙盒')
PIPE = os.path.join(W, '07_流水线')
WEB = os.path.join(W, '06_网站方案', 'prototype_v2.html')
GEN = os.path.join(W, '04_生成过程_脚本图表')
BASE = os.path.join(W, '03_参考模板_旧报告', '热膨胀系数.docx')

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server')
APP = os.path.join(OUT, 'app')

KEEP_PY = ('core.py', 'bridge.py', 'ir.py', 'render_docx.py', 'style.py')


def _cp(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def main():
    # 每次重新组装前清掉自检留下的残渣（projects 里的测试产物、__pycache__），保证发出去的是干净的
    for junk in (os.path.join(APP, 'pipeline', 'projects'),
                 os.path.join(APP, 'pipeline', '__pycache__')):
        shutil.rmtree(junk, ignore_errors=True)

    for sub in ('web', 'pipeline/experiments', 'pipeline/content', 'assets/figures',
                'assets/figures_tungsten'):
        os.makedirs(os.path.join(APP, sub), exist_ok=True)

    # 1) 前端
    _cp(WEB, os.path.join(APP, 'web', 'prototype_v2.html'))

    # 2) 引擎：核心模块 + 每套实验的 calc_/mock_/sections_/checks_
    n_py = 0
    for f in sorted(os.listdir(PIPE)):
        if not f.endswith('.py'):
            continue
        ok = f in KEEP_PY or f.startswith(('calc_', 'mock_', 'sections_', 'checks_'))
        if not ok or '.bak' in f:
            continue
        _cp(os.path.join(PIPE, f), os.path.join(APP, 'pipeline', f))
        n_py += 1

    # 3) 实验定义 + 正文
    for sub in ('experiments', 'content'):
        src = os.path.join(PIPE, sub)
        for f in sorted(os.listdir(src)):
            if f.endswith(('.json', '.md')):
                _cp(os.path.join(src, f), os.path.join(APP, 'pipeline', sub, f))
    # 光电 / 钨 两套正文当年写在 04 目录里，统一改名搬进 content/<id>.md（bridge 会优先读这里）
    for src_name, eid in (('content_draft.md', 'photo'), ('content_tungsten.md', 'tungsten')):
        src = os.path.join(GEN, src_name)
        if os.path.isfile(src):
            _cp(src, os.path.join(APP, 'pipeline', 'content', eid + '.md'))

    # 4) 插图（只带 fig_ 开头的成品图，不带原始扫描件）
    n_fig = 0
    for f in sorted(os.listdir(GEN)):
        if f.startswith('fig_') and f.endswith(('.png', '.jpg')):
            _cp(os.path.join(GEN, f), os.path.join(APP, 'assets', f))
            n_fig += 1
    for sub in ('figures', 'figures_tungsten'):
        src = os.path.join(GEN, sub)
        if not os.path.isdir(src):
            continue
        for f in sorted(os.listdir(src)):
            if f.endswith(('.png', '.jpg')):
                _cp(os.path.join(src, f), os.path.join(APP, 'assets', sub, f))
                n_fig += 1

    # 5) 排版骨架
    _cp(BASE, os.path.join(APP, 'assets', 'template.docx'))

    # 6) 顺手统计一下（别把 11MB 的原始照片带进去）
    total = 0
    for root, _dirs, files in os.walk(APP):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    print('[bundle] py=%d fig=%d  total=%.1f MB  -> %s'
          % (n_py, n_fig, total / 1048576.0, OUT))

    # 7) 自检：实验数
    exps = [f for f in os.listdir(os.path.join(APP, 'pipeline', 'experiments'))
            if f.endswith('.json')]
    names = []
    for f in sorted(exps):
        j = json.load(io.open(os.path.join(APP, 'pipeline', 'experiments', f), encoding='utf-8'))
        names.append(j.get('name'))
    print('[bundle] experiments=%d' % len(exps))
    for n in names:
        print('         - %s' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main())
