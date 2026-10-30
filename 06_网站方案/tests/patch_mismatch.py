# -*- coding: utf-8 -*-
r"""bridge：让模型报出照片里真正的实验名；对不上返回 mismatch；/render 空表给清楚提示。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\bridge.py'
s = io.open(P, encoding='utf-8').read()
orig = len(s)

# ---------- 1) PROMPT：加 detected_exp + 「对不上就别硬填」
old = '''2. 结构：{{"exp_id":"{eid}","tables":{{"t1":{{"cells":[[...]]}},"t2":{{"cells":[[...]]}},"t3":{{"cells":[[...]]}}}},"notes":["..."]}}'''
new = '''2. 结构：{{"exp_id":"{eid}","detected_exp":"照片顶部印着的实验名称（照抄，看不清就填空字符串）","tables":{{"t1":{{"cells":[[...]]}},"t2":{{"cells":[[...]]}},"t3":{{"cells":[[...]]}}}},"notes":["..."]}}
2a. **先看照片顶部印的实验名称**。如果它和上面「实验：」写的不是同一个实验，就把实测名称填进 detected_exp，
    并在 notes 里写「照片是《X》，与指定的《Y》不符」，tables 里所有 cells 一律留空、不要硬填。'''
assert s.count(old) == 1, 'PROMPT 的结构行未命中'
s = s.replace(old, new)
print('[OK] PROMPT 加 detected_exp')

# ---------- 2) 实验名模糊匹配
if 'def match_exp(' not in s:
    anchor = 'def table_brief(ed):'
    helper = '''KEYWORDS = {
    'photo': ('光电', '光电子', '普朗克'),
    'tungsten': ('钨', '逸出功', '里查孙'),
    'young': ('杨氏', '杨氏模量', '拉伸', '弹性模量', '光杠杆'),
}


def match_exp(name):
    """按关键词把照片里印的实验名认到我们的 exp_id 上，认不出返回 None。"""
    t = (name or '').replace(' ', '')
    if not t:
        return None
    for eid, keys in KEYWORDS.items():
        for k in keys:
            if k in t:
                return eid
    return None


'''
    assert s.count(anchor) == 1
    s = s.replace(anchor, helper + anchor)
    print('[OK] 加 match_exp()')

# ---------- 3) _recognize：不一致就返回 409 + 建议切换
old = """        res['exp_id'] = eid
        res.setdefault('notes', [])"""
new = """        res['exp_id'] = eid
        res.setdefault('notes', [])
        det = (res.get('detected_exp') or '').strip()
        sug = match_exp(det) if det else None
        if det and sug and sug != eid:
            return self._json({
                'error': '这张照片印的是《%s》，不是你现在选的《%s》。' % (det, ed.get('name')),
                'mismatch': True, 'detected': det, 'suggest': sug,
                'suggest_name': experiments()[sug].get('name'),
            }, 409)"""
assert s.count(old) == 1, '_recognize 的 exp_id 赋值未命中'
s = s.replace(old, new)
print('[OK] mismatch 检查')

# ---------- 4) /render：空表直接给出人话
if 'tables_empty' not in s:
    anchor = "    def _render(self, req):"
    helper = '''    @staticmethod
    def tables_empty(tables):
        if not tables:
            return True
        for v in tables.values():
            cells = (v or {}).get('cells') if isinstance(v, dict) else v
            if not cells:
                continue
            for row in cells:
                if isinstance(row, (list, tuple)) and any(c not in (None, '', ' ') for c in row):
                    return False
                if isinstance(row, (int, float)):
                    return False
        return True

'''
    assert s.count(anchor) == 1
    s = s.replace(anchor, helper + anchor)
    print('[OK] 加 tables_empty()')

old = "    def _render(self, req):\n"
new = ("    def _render(self, req):\n"
       "        if self.tables_empty((req or {}).get('tables')):\n"
       "            return self._json({'error': '还没有可用的数据表：这张照片没认出数字（可能拍虚了、反光，'\n"
       "                                       '或者不是这个实验的记录页）。回到上传屏换一张清楚的照片，'\n"
       "                                       '只拍表格区域、正对着拍。'}, 400)\n")
assert s.count(old) == 1
s = s.replace(old, new)
print('[OK] /render 空表拦截')

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[DONE] %d -> %d' % (orig, len(s)))
