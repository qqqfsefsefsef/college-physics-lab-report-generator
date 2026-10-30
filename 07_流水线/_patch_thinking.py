# -*- coding: utf-8 -*-
"""关掉思考模式（thinking=disabled）+ 用量台账。
根因：deepseek 模型思考模式默认开启（effort=high），思维链把 max_tokens 吃光，
      content 回空，finish_reason=length。
修法：请求体加 "thinking": {"type": "disabled"}；旧模型不认这个字段就自动降级重试。
"""
import io
import sys

P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\bridge.py'
s = io.open(P, encoding='utf-8').read()
orig = s

# ---------- 1. 用量台账：记录每次模型调用的 token 用量 ----------
anchor = "def call_detect(image_b64, mime, c, ed_map):"
usage_func = '''USAGE_LOG = os.path.join(HERE, 'projects', '_debug', 'usage.jsonl')


def log_usage(tag, model, usage, diag=None):
    """把一次模型调用的用量落盘 + 打到控制台，方便「在后台看见使用记录」。"""
    u = usage or {}
    rec = {
        'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
        'tag': tag,
        'model': model,
        'prompt_tokens': u.get('prompt_tokens'),
        'completion_tokens': u.get('completion_tokens'),
        'total_tokens': u.get('total_tokens'),
        'finish': (diag or {}).get('finish_reason'),
        'content_chars': (diag or {}).get('len_content'),
        'reasoning_chars': (diag or {}).get('len_reasoning'),
    }
    try:
        d = os.path.dirname(USAGE_LOG)
        if not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
        with io.open(USAGE_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(rec, ensure_ascii=False) + '\\n')
    except Exception:
        pass
    print('[usage] %s model=%s in=%s out=%s total=%s finish=%s' % (
        tag, model, rec['prompt_tokens'], rec['completion_tokens'],
        rec['total_tokens'], rec['finish']))
    return rec


def read_usage(n=20):
    try:
        with io.open(USAGE_LOG, encoding='utf-8') as f:
            lines = [l for l in f.read().splitlines() if l.strip()]
        out = [json.loads(l) for l in lines[-max(1, min(n, 200)):]]
        total = 0
        for r in out:
            total += (r.get('total_tokens') or 0)
        return {'ok': True, 'n': len(out), 'total_tokens': total, 'items': out}
    except Exception as e:
        return {'ok': True, 'n': 0, 'total_tokens': 0, 'items': [], 'note': str(e)}


'''
assert anchor in s
s = s.replace(anchor, usage_func + anchor, 1)

# ---------- 2. call_detect：关思考 + 放宽 max_tokens + 用量 ----------
old = """    body = {
        'model': c['model'], 'temperature': 0, 'max_tokens': 300,
        'messages': [{'role': 'user', 'content': [
            {'type': 'text', 'text': DETECT_PROMPT.format(menu=menu)},
            {'type': 'image_url', 'image_url': {'url': 'data:%s;base64,%s' % (mime, image_b64)}},
        ]}],
    }"""
new = """    body = {
        'model': c['model'], 'max_tokens': 1200,
        'thinking': {'type': 'disabled'},
        'messages': [{'role': 'user', 'content': [
            {'type': 'text', 'text': DETECT_PROMPT.format(menu=menu)},
            {'type': 'image_url', 'image_url': {'url': 'data:%s;base64,%s' % (mime, image_b64)}},
        ]}],
    }"""
assert old in s
s = s.replace(old, new, 1)

old = """    with urllib.request.urlopen(req, timeout=90) as r:
        payload = json.loads(r.read().decode('utf-8'))
    msg = ((payload.get('choices') or [{}])[0].get('message') or {})
    return (msg.get('content') or ''), (payload.get('usage') or {})"""
new = """    payload = _post_with_thinking(req, c)
    msg = ((payload.get('choices') or [{}])[0].get('message') or {})
    text = msg.get('content') or ''
    log_usage('detect', c['model'], payload.get('usage'),
              {'finish_reason': ((payload.get('choices') or [{}])[0]).get('finish_reason'),
               'len_content': len(text), 'len_reasoning': len(msg.get('reasoning_content') or '')})
    return text, (payload.get('usage') or {})"""
assert old in s
s = s.replace(old, new, 1)

# ---------- 3. call_vision：关思考 + 用量 ----------
old = """    body = {
        'model': c['model'],
        'temperature': 0,
        'max_tokens': 8000,"""
new = """    body = {
        'model': c['model'],
        'thinking': {'type': 'disabled'},
        'max_tokens': 8000,"""
assert old in s
s = s.replace(old, new, 1)

old = """    with urllib.request.urlopen(req, timeout=180) as r:
        payload = json.loads(r.read().decode('utf-8'))
    ch = (payload.get('choices') or [{}])[0]"""
new = """    payload = _post_with_thinking(req, c)
    ch = (payload.get('choices') or [{}])[0]"""
assert old in s
s = s.replace(old, new, 1)

# 用量记账 + 思考模式兜底提示
old = """    if not text and think:
        diag['hint'] = '模型把内容都写进了思考过程（reasoning_content），content 为空'"""
new = """    log_usage('recognize:' + str(ed.get('id')), c['model'], diag.get('usage'), diag)
    if not text and think:
        diag['hint'] = ('模型把内容都写进了思考过程（reasoning_content），content 为空；'
                        '本请求已带 thinking=disabled，若仍如此请把 max_tokens 调大')"""
assert old in s
s = s.replace(old, new, 1)

# ---------- 4. 通用 POST：thinking 被拒时自动降级 ----------
anchor2 = "def call_detect(image_b64, mime, c, ed_map):"
post_func = '''def _post_with_thinking(req, c):
    """发请求；若服务端不认 thinking 字段（400/422）就摘掉它重发一次。

    思考模式默认开启且 effort=high，会把 max_tokens 全吃进思维链、content 回空
    （见 deepseek-ai/DeepSeek-V3#1610）。这里统一关掉；老模型不认就降级。
    """
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        detail = ''
        try:
            detail = e.read().decode('utf-8', 'replace')[:400]
        except Exception:
            pass
        if e.code in (400, 422) and ('thinking' in detail.lower() or 'unknown' in detail.lower()):
            body = json.loads(req.data.decode('utf-8'))
            body.pop('thinking', None)
            body['reasoning_effort'] = 'low'
            req2 = urllib.request.Request(
                req.full_url, data=json.dumps(body).encode('utf-8'),
                headers=dict(req.headers), method='POST')
            with urllib.request.urlopen(req2, timeout=180) as r:
                return json.loads(r.read().decode('utf-8'))
        raise RuntimeError('模型接口返回 %s：%s' % (e.code, detail or e.reason))


'''
assert anchor2 in s
s = s.replace(anchor2, post_func + anchor2, 1)

# ---------- 5. /ping 也关思考 ----------
old = """        body = {'model': model, 'max_tokens': 1, 'temperature': 0,
                'messages': [{'role': 'user', 'content': 'ping'}]}"""
new = """        body = {'model': model, 'max_tokens': 1, 'thinking': {'type': 'disabled'},
                'messages': [{'role': 'user', 'content': 'ping'}]}"""
assert old in s
s = s.replace(old, new, 1)

# ---------- 6. GET /usage ----------
old = """        if parsed.path == '/file':"""
new = """        if parsed.path == '/usage':
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            return self._json(read_usage(int((q.get('n') or ['20'])[0] or 20)))
        if parsed.path == '/file':"""
assert old in s
s = s.replace(old, new, 1)

assert s != orig
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[OK] bridge.py patched, %d -> %d chars' % (len(orig), len(s)))
