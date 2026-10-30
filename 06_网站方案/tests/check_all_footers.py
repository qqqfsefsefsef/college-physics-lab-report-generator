# -*- coding: utf-8 -*-
r"""页脚改造后的终检：三份生成件 + 两份参考件。"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
from docx import Document  # noqa: E402

W = r'C:\Users\lidey\Desktop\实验报告制作沙盒'
TARGETS = [
    (W + r'\05_成品_报告\光电效应的研究.docx', '生成件（Word 版）'),
    (W + r'\05_成品_报告\光电效应的研究_网页流水线版.docx', '生成件（网页流水线）'),
    (W + r'\05_成品_报告\钨的逸出功测定.docx', '生成件（钨）'),
    (W + r'\07_流水线\projects\young-demo\out\杨氏模量.docx', '生成件（杨氏模量）'),
    (W + r'\03_参考模板_旧报告\热膨胀系数.docx', '参考模板（不动）'),
    (W + r'\03_参考模板_旧报告\霍尔效应-已填数据.docx', '参考模板（不动）'),
]
for p, tag in TARGETS:
    d = Document(p)
    foot = ' | '.join(x.text.strip() for s in d.sections for x in s.footer.paragraphs if x.text.strip())
    head = ' | '.join(x.text.strip() for s in d.sections for x in s.header.paragraphs if x.text.strip())
    imgs = sum(1 for s in d.inline_shapes)
    chars = sum(len(x.text) for x in d.paragraphs)
    print('%-30s %-12s foot=%-10s paras=%-4d tables=%d imgs=%d chars=%d'
          % (os.path.basename(p)[:30], tag, foot[:10], len(d.paragraphs), len(d.tables), imgs, chars))
    assert head.startswith('南京信息工程大学'), '页眉丢了'
