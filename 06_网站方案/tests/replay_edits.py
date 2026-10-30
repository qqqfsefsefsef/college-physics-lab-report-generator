r"""从 decompress 出来的会话记录里，把 prototype_v2.html 的 write/edit 重新回放到磁盘。

用法：
  python replay_edits.py <记录文件> [<记录文件> ...]   # 按给的顺序回放
第一条记录里必须含一次完整的 write（初始版本）。
"""
import json
import os
import re
import sys

TARGET = 'prototype_v2.html'
OUT = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'


def find_json_after(text, key, start=0):
    """在 text 里找含 key 的 JSON 对象，从 '{' 开始用 raw_decode 解。"""
    hits = []
    for m in re.finditer(r'\{"(?:content|file_path)"', text):
        if m.start() < start:
            continue
        try:
            obj, end = json.JSONDecoder().raw_decode(text, m.start())
        except Exception:
            continue
        blob = json.dumps(obj, ensure_ascii=False)
        if key in blob:
            hits.append((m.start(), end, obj))
    return hits


def main(files):
    content = None
    applied = []
    for f in files:
        text = open(f, encoding='utf-8').read()
        for start, end, obj in find_json_after(text, TARGET):
            fp = obj.get('file_path') or ''
            if TARGET not in fp:
                continue
            if 'content' in obj:
                content = obj['content']
                applied.append(('write', len(content)))
            elif 'old_string' in obj and 'new_string' in obj:
                if content is None:
                    print('!! 还没有 base，跳过 edit')
                    continue
                old, new = obj['old_string'], obj['new_string']
                if old in content:
                    n = content.count(old)
                    content = content.replace(old, new, 1)
                    applied.append(('edit', n))
                else:
                    applied.append(('MISS', old[:40]))
    if content is None:
        print('没找到 base write')
        return 1
    open(OUT, 'w', encoding='utf-8', newline='\n').write(content)
    print('wrote %d chars -> %s' % (len(content), OUT))
    for a in applied:
        print('  ', a)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
