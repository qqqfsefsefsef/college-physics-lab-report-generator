# -*- coding: utf-8 -*-
"""IR 层：实验定义 + calc.json + 正文 md → block 列表 → 交给渲染器。

新实验要做的只有两件事：写 experiments/<id>.json、写 sections_<id>.py。
渲染器（render_docx.py）与这里的分节骨架都不用动——这就是「接第二个实验」的考题。
"""
import argparse
import importlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import render_docx  # noqa: E402

SEC_RE = re.compile(r'^===\s*(.+?)\s*===$')


def parse_md(path):
    """返回 {节名: [段落文本, ...]}；占位符 [[F1]] 会作为独立段落保留。"""
    if not os.path.exists(path):
        return {}
    out, cur = {}, None
    buf = []

    def flush():
        if buf and cur:
            out.setdefault(cur, []).append('\n'.join(buf).strip())
        buf.clear()

    for raw in open(path, encoding='utf-8').read().splitlines():
        m = SEC_RE.match(raw.strip())
        if m:
            flush()
            cur = m.group(1)
            out.setdefault(cur, [])
        elif not raw.strip():
            flush()
        else:
            buf.append(raw.strip())
    flush()
    return out


PFX_RE = re.compile(r'^(F\d+)[\s\u3000]+(\S.*)$')


def expand_placeholders(blocks, formulas):
    out = []
    for b in blocks:
        if b['t'] == 'para':
            txt = b['text'].strip()
            m = re.fullmatch(r'\[\[(F\d+)\]\]', txt)
            if not m:
                # 正文里直接写「F1  公式文本」也算，统一换成规范写法
                m = PFX_RE.match(txt)
            if m and m.group(1) in formulas:
                out.append({'t': 'formula', 'expr': formulas[m.group(1)]})
                continue
        out.append(b)
    return out


def build(exp, calc, md_path, assets=None):
    """assets: {'shot': 学习通截图路径, 'hw': 作业文件路径…}，由 bridge 传进来。"""
    md = parse_md(md_path)
    assets = assets or {}
    exp = dict(exp)
    if assets.get('shot'):
        exp['_shot'] = assets['shot']
    mod = importlib.import_module('sections_' + exp['id'])
    blocks = mod.build(exp, calc, md)
    return expand_placeholders(blocks, exp.get('formulas', {}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--exp', required=True)
    ap.add_argument('--calc', required=True)
    ap.add_argument('--md', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--blocks', default='')
    ap.add_argument('--title', default='')
    a = ap.parse_args()

    exp = json.load(open(a.exp, encoding='utf-8'))
    calc = json.load(open(a.calc, encoding='utf-8'))
    blocks = build(exp, calc, a.md)
    if a.blocks:
        json.dump(blocks, open(a.blocks, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    title = a.title or exp.get('title', '')
    render_docx.render(blocks, a.out, title)
    n_tab = sum(1 for b in blocks if b['t'] == 'table')
    n_fig = sum(1 for b in blocks if b['t'] == 'figure')
    n_fml = sum(1 for b in blocks if b['t'] == 'formula')
    print('[OK] blocks=%d (table %d, formula %d, figure %d) → %s'
          % (len(blocks), n_tab, n_fml, n_fig, a.out))


if __name__ == '__main__':
    main()
