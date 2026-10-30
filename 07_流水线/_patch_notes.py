# -*- coding: utf-8 -*-
"""把识别返回的 notes 结构化：每个疑点带上「表/行/列/位置/当前值/候选值」。

页面要把它渲染成一道道选择题，所以必须能定位到具体格子。
"""
import io

P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\bridge.py'
s = io.open(P, encoding='utf-8').read()
orig = s

# ---------- 1. PROMPT：notes 改成结构化对象 ----------
old = '''2. 结构：{{"exp_id":"{eid}","detected_exp":"照片顶部印着的实验名称（照抄，看不清就填空字符串）","tables":{{"t1":{{"cells":[[...]]}},"t2":{{"cells":[[...]]}},"t3":{{"cells":[[...]]}}}},"notes":["..."]}}'''
new = '''2. 结构：{{"exp_id":"{eid}","detected_exp":"照片顶部印着的实验名称（照抄，看不清就填空字符串）",
   "tables":{{"t1":{{"cells":[[...]]}},"t2":{{"cells":[[...]]}},"t3":{{"cells":[[...]]}}}},
   "notes":[{{"table":"t1","row":2,"col":1,"where":"表1 · 546.1nm/4mm · U_AK=−4 V 那一格",
             "current":"0.5","candidates":["0.5","0.4"],"why":"有涂改"}}]}}'''
assert old in s
s = s.replace(old, new, 1)

old = '''4. 每个数字旁边若看不清/被涂改/有歧义，在 notes 里写明位置和你的两个候选值。'''
new = '''4. 每个数字旁边若看不清/被涂改/有歧义，就在 notes 里加一条：
   - `table` 填 t1/t2/t3，`row` `col` 是**该格在 cells 二维数组里的下标（从 0 开始，不含表头）**；
   - `where` 用人话写清位置（哪张表、哪个波长/光圈、哪一列），要能让读者一眼找到纸上那一格；
   - `current` 是你最终填进 cells 的值；`candidates` 给 2~3 个你可能搞混的值（**第一个必须等于 current**）；
   - `why` 一句话说明为什么不确定（涂改/字迹/压线…）。
   如果 notes 里的题点你没法精确定位到格子，就把 row/col 填 -1，别瞎编下标。'''
assert old in s
s = s.replace(old, new, 1)

# ---------- 2. 归一化函数 ----------
anchor = "def _balanced(s, i):"
norm = '''def norm_notes(ed, tables, notes):
    """把模型给的 notes 统一成结构化题点；能定位就带上 table/row/col。"""
    out = []
    cells_of = {}
    for tid, tb in (tables or {}).items():
        if isinstance(tb, dict) and isinstance(tb.get('cells'), list):
            cells_of[tid] = tb['cells']
    for k, n in enumerate(notes or []):
        if isinstance(n, str):
            n = {'why': n}
        if not isinstance(n, dict):
            continue
        tid = str(n.get('table') or '').strip()
        try:
            row = int(n.get('row'))
        except Exception:
            row = -1
        try:
            col = int(n.get('col'))
        except Exception:
            col = -1
        cur = n.get('current')
        cands = n.get('candidates') or []
        if not isinstance(cands, list):
            cands = [cands]
        cands = [str(c).strip() for c in cands if str(c).strip() not in ('', 'None')]
        if cur is not None and str(cur).strip() not in cands:
            cands.insert(0, str(cur).strip())
        # 有 cells 就从表里回填当前值，避免模型自相矛盾
        real = None
        if tid in cells_of and row >= 0 and col >= 0:
            try:
                real = cells_of[tid][row][col]
            except Exception:
                real = None
        if real is not None and str(real).strip():
            cur = str(real).strip()
            if cur not in cands:
                cands.insert(0, cur)
        item = {
            'id': 'q%d' % k,
            'table': tid if tid in cells_of else '',
            'row': row,
            'col': col,
            'where': str(n.get('where') or '').strip(),
            'current': '' if cur is None else str(cur).strip(),
            'candidates': cands[:4],
            'why': str(n.get('why') or n.get('msg') or '').strip(),
        }
        if not item['where']:
            item['where'] = ('%s 第 %d 行第 %d 列' % (tid, row + 1, col + 1)
                             if item['table'] else '（模型没写清位置）')
        out.append(item)
    return out


'''
assert anchor in s
s = s.replace(anchor, norm + anchor, 1)

# ---------- 3. 在返回结果里把 notes 换成结构化版本 ----------
old = """        res['meta'] = {'mode': 'mock', 'model': None, 'usage': {}, 'image': imeta}
            return self._json(res)"""
new = """        res['notes'] = norm_notes(ed, res.get('tables') or {}, res.get('notes'))
            res['meta'] = {'mode': 'mock', 'model': None, 'usage': {}, 'image': imeta}
            return self._json(res)"""
if old in s:
    s = s.replace(old, new, 1)
else:
    old = """            res = mock_result(ed)
            res['meta'] = {'mode': 'mock', 'model': None, 'usage': {}, 'image': imeta}
            return self._json(res)"""
    new = """            res = mock_result(ed)
            res['notes'] = norm_notes(ed, res.get('tables') or {}, res.get('notes'))
            res['meta'] = {'mode': 'mock', 'model': None, 'usage': {}, 'image': imeta}
            return self._json(res)"""
    assert old in s, 'mock block not found'
    s = s.replace(old, new, 1)

assert s != orig
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[OK] bridge notes normalized, %d -> %d chars' % (len(orig), len(s)))
