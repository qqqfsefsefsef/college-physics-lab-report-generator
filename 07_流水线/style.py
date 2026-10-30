# -*- coding: utf-8 -*-
"""作业风格卡：从用户以前写过的实验报告（.docx）里抽「他/她是怎么写的」。

只抽**可量化、可校验**的东西，不做主观发挥：
  - 篇幅与句长（总字数、句数、平均句长、长短句占比）
  - 人称与语气（第一/第三人称、我们、我觉得/感觉/发现…）
  - 连接词偏好（然后/所以/但是/因为/因此/其实/于是…）
  - 段落习惯（段数、平均段长、段首常用词）
  - 标点偏好（破折号、分号、括号、引号、感叹号）
  - 高频 2-gram（看不出分词也能抓到「实验数据」「误差分析」这种口头习惯）

输出既能直接给人看（summary 一段话），也能喂给模型当 few-shot 提示（prompt_hints）。

命令行：python style.py <hw.docx> [out.json]
"""
import json
import re
import sys

from docx import Document

CONNECTIVES = [
    '然后', '所以', '但是', '而且', '因为', '因此', '其实', '于是', '不过', '并且',
    '就是说', '也就是', '另外', '此外', '同时', '接着', '首先', '其次', '最后',
    '总之', '换句话说', '反而', '虽然', '如果', '只要', '一旦', '结果', '发现',
]
FEELING = ['我觉得', '我感觉', '我认为', '我意识到', '才发现', '才知道', '感觉', '觉得',
           '比较', '有点', '挺', '特别', '非常', '大概', '可能', '应该', '其实']
PUNCT = {'破折号': '——', '分号': '；', '括号': '（', '引号': '“', '感叹号': '！', '问号': '？'}


def _paras(doc):
    """只要正文段落（不掺表格里的数字，否则「段首词」「句长」全被污染）。"""
    out = []
    for p in doc.paragraphs:
        t = (p.text or '').strip()
        if t:
            out.append(t)
    return out


def _cell_text(doc):
    out = []
    for tb in doc.tables:
        for row in tb.rows:
            for c in row.cells:
                t = (c.text or '').strip()
                if t and len(t) > 3:
                    out.append(t)
    return out


def _sentences(text):
    parts = re.split(r'[。！？!?；;]', text)
    return [p.strip() for p in parts if len(p.strip()) >= 2]


def card(path, max_chars=60000):
    doc = Document(path)
    paras = _paras(doc)
    body = '\n'.join(paras)[:max_chars]
    chars = len(re.sub(r'\s', '', body))
    sents = _sentences(body)
    lens = [len(re.sub(r'\s', '', s)) for s in sents] or [0]
    n = len(lens)
    avg = sum(lens) / float(n)
    short = sum(1 for x in lens if x <= 12) / float(n)
    long_ = sum(1 for x in lens if x >= 40) / float(n)

    def cnt(words):
        return {w: body.count(w) for w in words if body.count(w)}

    conn = dict(sorted(cnt(CONNECTIVES).items(), key=lambda kv: -kv[1])[:8])
    feel = dict(sorted(cnt(FEELING).items(), key=lambda kv: -kv[1])[:8])
    punct = {k: body.count(v) for k, v in PUNCT.items()}
    punct = {k: v for k, v in punct.items() if v}

    # 高频 2-gram（滑窗，去重且只留出现 ≥3 次的）
    g = {}
    zh = re.sub(r'[^\u4e00-\u9fa5]', ' ', body)
    for seg in zh.split():
        for i in range(len(seg) - 1):
            k = seg[i:i + 2]
            g[k] = g.get(k, 0) + 1
    grams = [k for k, v in sorted(g.items(), key=lambda kv: -kv[1])[:40] if v >= 3][:15]

    heads = {}
    for p in paras:
        h = re.sub(r'^[\d０-９().、，,\s【】]+', '', p)[:4]
        if len(h) >= 2 and re.search(r'[\u4e00-\u9fa5]', h):
            heads[h] = heads.get(h, 0) + 1
    heads = dict(sorted(heads.items(), key=lambda kv: -kv[1])[:8])

    # 人称：看「有多少段落用了我」比看总字数更准（体会段满篇我、原理段没有）
    fp_paras = sum(1 for p in paras if '我' in p)
    fp_ratio = fp_paras / float(max(len(paras), 1))
    first_person = body.count('我') / float(max(chars, 1)) * 1000  # 每千字出现次数
    stats = {
        'chars': chars,
        'paras': len(paras),
        'sentences': n,
        'avg_sentence': round(avg, 1),
        'short_ratio': round(short, 3),
        'long_ratio': round(long_, 3),
        'avg_para_chars': round(chars / float(max(len(paras), 1)), 1),
        'first_person_per_1k': round(first_person, 1),
        'first_person_para_ratio': round(fp_ratio, 3),
        'connectives': conn,
        'feeling': feel,
        'punct': punct,
        'bigrams': grams,
        'para_heads': heads,
    }

    tone = '第一人称口语' if fp_ratio >= 0.35 else (
        '第一人称克制' if fp_ratio >= 0.12 else '第三人称书面')
    rhythm = '短句为主' if avg <= 15 else ('长短交错' if avg <= 28 else '长句铺陈')
    summary = '他/她的报告约 %d 字、%d 段、%d 句，平均句长 %.1f 字（%s，%s）；%s；%s' % (
        chars, len(paras), n, avg, rhythm, tone,
        ('偏爱这些连接词：' + '、'.join(list(conn)[:5])) if conn else '连接词用得少',
        ('口头习惯：' + '、'.join(grams[:6])) if grams else '无明显高频短语')

    hints = [
        '平均句长约 %.0f 字，%s' % (avg, rhythm),
        '人称与语气：%s（%.0f%% 的段落用到「我」）' % (tone, fp_ratio * 100),
        ('常用连接词：' + '、'.join(conn)) if conn else '连接词用得很少，句子之间靠内容衔接',
        ('口语化表达：' + '、'.join(feel)) if feel else '不口语化',
        ('标点偏好：' + '、'.join('%s×%d' % (k, v) for k, v in punct.items())) if punct else '标点朴素',
        ('段落常以这些词开头：' + '、'.join(heads)) if heads else '',
        '硬约束：不得复用他原文里连续 12 个字以上的片段',
    ]
    hints = [h for h in hints if h]
    return {'ok': True, 'file': path.split('\\')[-1], 'summary': summary,
            'stats': stats, 'prompt_hints': hints}


def main():
    if len(sys.argv) < 2:
        raise SystemExit('用法：python style.py <hw.docx> [out.json]')
    path = sys.argv[1]
    c = card(path)
    if len(sys.argv) > 2:
        json.dump(c, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('written ' + sys.argv[2])
    else:
        print(json.dumps(c, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
