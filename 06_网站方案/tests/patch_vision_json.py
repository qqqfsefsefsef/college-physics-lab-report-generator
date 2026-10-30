# -*- coding: utf-8 -*-
r"""修「模型没有返回 JSON」：放宽 token、稳健抠 JSON、失败时把诊断信息带回来、自动重试一次。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\bridge.py'
s = io.open(P, encoding='utf-8').read()
orig = len(s)

# ---------- 1) call_vision：加大 max_tokens，返回 finish_reason / 思考内容，并留一份原始响应
old_call = s[s.index('def call_vision('):s.index('def parse_json_loose(')]
new_call = '''def call_vision(ed, image_b64, mime, c, strict=False):
    """调一次视觉模型。strict=True 时用更硬的「只输出 JSON」提示，用于重试。"""
    text_prompt = PROMPT.format(name=ed.get('name', ''), no=ed.get('no', ''),
                                brief=table_brief(ed), eid=ed['id'])
    if strict:
        text_prompt += ('\\n\\n【重要】只输出一个 JSON 对象本身，不要解释、不要 markdown 代码块、'
                        '不要任何前后缀。所有数字用阿拉伯数字，不要写单位。')
    body = {
        'model': c['model'],
        'temperature': 0,
        'max_tokens': 8000,
        'messages': [{
            'role': 'user',
            'content': [
                {'type': 'text', 'text': text_prompt},
                {'type': 'image_url', 'image_url': {'url': 'data:%s;base64,%s' % (mime, image_b64)}},
            ],
        }],
    }
    req = urllib.request.Request(
        c['base_url'] + '/chat/completions',
        data=json.dumps(body).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + c['key']},
        method='POST')
    with urllib.request.urlopen(req, timeout=180) as r:
        payload = json.loads(r.read().decode('utf-8'))
    ch = (payload.get('choices') or [{}])[0]
    msg = ch.get('message') or {}
    text = msg.get('content') or ''
    think = msg.get('reasoning_content') or ''
    diag = {'finish_reason': ch.get('finish_reason'),
            'len_content': len(text), 'len_reasoning': len(think),
            'usage': payload.get('usage') or {}}
    if not text and think:
        diag['hint'] = '模型把内容都写进了思考过程（reasoning_content），content 为空'
    # 留一份原始响应，排障用
    try:
        d = os.path.join(HERE, 'projects', '_debug')
        os.makedirs(d, exist_ok=True)
        fn = os.path.join(d, 'last_vision.json')
        io.open(fn, 'w', encoding='utf-8').write(json.dumps(
            {'ts': time.strftime('%Y-%m-%d %H:%M:%S'), 'model': c['model'],
             'diag': diag, 'content': text[:4000], 'reasoning': think[:2000]},
            ensure_ascii=False, indent=1))
        diag['raw_saved'] = fn
    except Exception:
        pass
    return text, (payload.get('usage') or {}), diag


'''
s = s.replace(old_call, new_call)
print('[OK] call_vision 改好')

# ---------- 2) parse_json_loose：剥代码块 + 配对括号找第一个完整对象
old_parse = s[s.index('def parse_json_loose('):s.index('# ---------------------------------------------------------------- 桩数据')]
new_parse = '''def _balanced(s, i):
    """从 s[i]=='{' 开始，找出配对的右括号位置（跳过字符串里的括号）。"""
    depth, ins, esc = 0, False, False
    for k in range(i, len(s)):
        ch = s[k]
        if ins:
            if esc:
                esc = False
            elif ch == '\\\\':
                esc = True
            elif ch == '"':
                ins = False
            continue
        if ch == '"':
            ins = True
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return k
    return -1


def parse_json_loose(text):
    """模型常包 ```json 或前后加解释，这里宽松地抠出第一个完整 JSON 对象。"""
    if not text or not text.strip():
        raise ValueError('模型返回了空内容（可能是思考把 token 用完了，或该模型不支持图片输入）')
    t = text.strip()
    t = re.sub(r'^```[a-zA-Z]*\\s*', '', t)
    t = re.sub(r'\\s*```$', '', t)
    try:
        return json.loads(t)
    except Exception:
        pass
    i = t.find('{')
    if i < 0:
        raise ValueError('模型没有返回 JSON（内容开头：%s）' % t[:160].replace('\\n', ' '))
    j = _balanced(t, i)
    if j < 0:
        raise ValueError('模型返回的 JSON 不完整（可能被截断，长度 %d，开头：%s）'
                         % (len(t), t[:160].replace('\\n', ' ')))
    return json.loads(t[i:j + 1])


'''
s = s.replace(old_parse, new_parse)
print('[OK] parse_json_loose 改好')

# ---------- 3) _recognize：失败自动重试一次，并把诊断信息带回去
old_try = """        try:
            text, usage = call_vision(ed, img, mime, c)
            res = parse_json_loose(text)
        except urllib.error.HTTPError as e:
            detail = e.read().decode('utf-8', 'replace')[:400]
            return self._json({'error': '模型接口返回 %s：%s' % (e.code, detail)}, 502)
        except Exception as e:
            return self._json({'error': '识别失败：%s' % e}, 502)"""
new_try = """        diag = {}
        try:
            text, usage, diag = call_vision(ed, img, mime, c)
            res = parse_json_loose(text)
        except urllib.error.HTTPError as e:
            detail = e.read().decode('utf-8', 'replace')[:400]
            return self._json({'error': '模型接口返回 %s：%s' % (e.code, detail)}, 502)
        except Exception as e:
            first = str(e)
            # 第二次：换成更硬的「只输出 JSON」提示再试一遍
            try:
                text2, usage2, diag2 = call_vision(ed, img, mime, c, strict=True)
                res = parse_json_loose(text2)
                usage = usage2 or usage
                diag = diag2 or diag
                diag['retried'] = True
            except Exception as e2:
                return self._json({'error': str(e2),
                                   'first_error': first,
                                   'diag': {**(diag or {}), 'retry_error': str(e2),
                                            'retried': True}}, 502)"""
assert s.count(old_try) == 1, '_recognize 的重试块未命中'
s = s.replace(old_try, new_try)
print('[OK] _recognize 加了重试')

# ---------- 4) meta 里带上诊断
old_meta = """        res['meta'] = {'mode': 'real', 'model': c['model'], 'usage': usage,
                       'bytes': len(img) * 3 // 4, 'image': imeta}"""
new_meta = """        res['meta'] = {'mode': 'real', 'model': c['model'], 'usage': usage,
                       'bytes': len(img) * 3 // 4, 'image': imeta,
                       'diag': diag or {}}"""
assert s.count(old_meta) == 1
s = s.replace(old_meta, new_meta)
print('[OK] meta 带 diag')

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[DONE] %d -> %d 字符' % (orig, len(s)))
