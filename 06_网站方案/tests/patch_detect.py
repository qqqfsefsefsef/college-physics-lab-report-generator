# -*- coding: utf-8 -*-
r"""bridge 新增 /detect：先看照片是哪个实验，再决定用哪套表格去认。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\bridge.py'
s = io.open(P, encoding='utf-8').read()
orig = len(s)

# ---------- 1) 识别实验的提示词 + 调用
if 'DETECT_PROMPT' not in s:
    anchor = 'def call_vision('
    block = '''DETECT_PROMPT = """你是一个实验报告识别器。这是一张大学物理实验「原始数据记录页」的照片。

请判断它属于下面哪一个实验（只看照片上印的实验名称、表格结构和公式）：
{menu}

只输出 JSON，不要解释、不要代码块：
{{"exp_id":"列表里的 id；判断不了就填空字符串","detected":"照片上印的实验名称，照抄","evidence":"一句话理由"}}
"""


def call_detect(image_b64, mime, c, ed_map):
    menu = '\\n'.join('- %s：%s（%s）' % (k, v.get('name'), v.get('no') or '')
                     for k, v in ed_map.items())
    body = {
        'model': c['model'], 'temperature': 0, 'max_tokens': 300,
        'messages': [{'role': 'user', 'content': [
            {'type': 'text', 'text': DETECT_PROMPT.format(menu=menu)},
            {'type': 'image_url', 'image_url': {'url': 'data:%s;base64,%s' % (mime, image_b64)}},
        ]}],
    }
    req = urllib.request.Request(
        c['base_url'] + '/chat/completions',
        data=json.dumps(body).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + c['key']},
        method='POST')
    with urllib.request.urlopen(req, timeout=90) as r:
        payload = json.loads(r.read().decode('utf-8'))
    msg = ((payload.get('choices') or [{}])[0].get('message') or {})
    return (msg.get('content') or ''), (payload.get('usage') or {})


'''
    assert s.count(anchor) == 1
    s = s.replace(anchor, block + anchor)
    print('[OK] 加 DETECT_PROMPT / call_detect')

# ---------- 2) 路由 + handler
if "'/detect'" not in s:
    anchor = "        if path == '/recognize':"
    s = s.replace(anchor, "        if path == '/detect':\n            return self._detect(req)\n" + anchor, 1)
    print('[OK] 路由加 /detect')

if 'def _detect(self, req):' not in s:
    anchor = "    # -------- /recognize"
    handler = '''    # -------- /detect  先认这是哪个实验
    def _detect(self, req):
        exps = experiments()
        img = req.get('image_b64') or ''
        mime = req.get('mime') or 'image/jpeg'
        if not img:
            return self._json({'error': '没有收到图片'}, 400)
        try:
            raw = base64.b64decode(img)
            img, mime, imeta = normalize_image(raw, mime)
        except HeicError as e:
            return self._json({'error': str(e), 'hint': 'HEIC 转码失败，可用「照片」另存为 JPG 再传。'}, 415)
        except Exception as e:
            return self._json({'error': '这张图读不出来（%s）。' % e}, 415)
        b64 = base64.b64encode(img).decode('ascii')

        if self.server.mock or req.get('mode') == 'mock':
            return self._json({'ok': True, 'exp_id': 'photo', 'name': exps['photo'].get('name'),
                               'detected': '（桩）光电效应的研究', 'evidence': '桩模式固定返回光电效应',
                               'candidates': list(exps), 'image': imeta, 'mode': 'mock'})

        c = conf()
        key = (req.get('api_key') or '').strip() or c['key']
        base = ((req.get('base_url') or '').strip() or c['base_url']).rstrip('/')
        model = (req.get('model') or '').strip() or c['model']
        if not key:
            return self._json({'error': '还没有密钥：先在「接入自己的 API」里填一次。'}, 400)
        try:
            text, usage = call_detect(b64, mime, {'key': key, 'base_url': base, 'model': model}, exps)
            res = parse_json_loose(text)
        except urllib.error.HTTPError as e:
            return self._json({'error': '模型接口返回 %s：%s' % (e.code, e.read().decode('utf-8', 'replace')[:300])}, 502)
        except Exception as e:
            return self._json({'ok': False, 'error': str(e), 'candidates': list(exps),
                               'image': imeta}, 200)

        eid = (res.get('exp_id') or '').strip()
        detected = (res.get('detected') or '').strip()
        if eid not in exps:
            eid = match_exp(detected) or ''
        if not eid:
            return self._json({'ok': False, 'detected': detected, 'evidence': res.get('evidence', ''),
                               'candidates': list(exps), 'image': imeta, 'usage': usage}, 200)
        return self._json({'ok': True, 'exp_id': eid, 'name': exps[eid].get('name'),
                           'detected': detected or exps[eid].get('name'),
                           'evidence': res.get('evidence', ''), 'candidates': list(exps),
                           'image': imeta, 'usage': usage, 'mode': 'real'})

'''
    assert s.count(anchor) == 1, '/recognize 锚点未命中'
    s = s.replace(anchor, handler + anchor)
    print('[OK] 加 _detect()')

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[DONE] %d -> %d' % (orig, len(s)))
