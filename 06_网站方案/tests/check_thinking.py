# -*- coding: utf-8 -*-
"""验证「关思考模式」真的发出去了（不联网，桩掉 urlopen）。"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线')

import bridge  # noqa: E402

ok_n = 0
fail_n = 0


def ok(name, cond, detail=''):
    global ok_n, fail_n
    if cond:
        ok_n += 1
        print('[OK] %s  %s' % (name, detail))
    else:
        fail_n += 1
        print('[FAIL] %s  %s' % (name, detail))


seen = []


class FakeResp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode('utf-8')

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def fake_urlopen(req, timeout=None):
    body = json.loads(req.data.decode('utf-8'))
    seen.append(body)
    txt = json.dumps(body.get('messages'), ensure_ascii=False)
    # 实验识别那一类请求（提示词里带 exp_id 菜单）回正常 JSON
    if 'exp_id' in txt and body.get('max_tokens', 0) < 2000:
        return FakeResp({'choices': [{'finish_reason': 'stop',
                                      'message': {'content': '{"exp_id":"photo"}'}}],
                         'usage': {'prompt_tokens': 1200, 'completion_tokens': 12,
                                   'total_tokens': 1212}})
    # 其余模拟「思考把 token 吃光」的响应
    return FakeResp({
        'choices': [{'finish_reason': 'length',
                     'message': {'content': '', 'reasoning_content': '想' * 500}}],
        'usage': {'prompt_tokens': 1500, 'completion_tokens': 8000, 'total_tokens': 9500},
    })


bridge.urllib.request.urlopen = fake_urlopen

cfg = {'key': 'sk-test', 'base_url': 'https://api.deepseek.com/v1',
       'model': 'deepseek-v4-flash-vision-exp'}
exp_map = bridge.experiments()
ed = exp_map['photo']

# 1) /recognize 用的 call_vision
text, usage, diag = bridge.call_vision(ed, 'AAAA', 'image/jpeg', cfg)
body = seen[-1]
ok('识别请求带 thinking=disabled', body.get('thinking') == {'type': 'disabled'}, str(body.get('thinking')))
ok('识别请求 max_tokens >= 8000', body.get('max_tokens', 0) >= 8000, str(body.get('max_tokens')))
ok('识别请求不再传 temperature', 'temperature' not in body, str(body.get('temperature')))
ok('空正文被识别并给出提示',
   text == '' and (diag.get('finish_reason') == 'length') and ('思考' in (diag.get('hint') or '')),
   repr(diag.get('hint'))[:60])

# 2) /detect 用的 call_detect
exp_map = {'photo': ed}
bridged_text, u2 = bridge.call_detect('AAAA', 'image/jpeg', cfg, exp_map)
body2 = seen[-1]
ok('实验识别请求带 thinking=disabled', body2.get('thinking') == {'type': 'disabled'}, str(body2.get('thinking')))
ok('实验识别 max_tokens 放宽到 >= 800', body2.get('max_tokens', 0) >= 800, str(body2.get('max_tokens')))
ok('实验识别能取到 JSON', '"exp_id"' in bridged_text, bridged_text[:40])

# 3) 用量台账
rec = bridge.read_usage(10)
ok('用量台账记到条目', rec['n'] >= 2, 'n=%s total=%s' % (rec['n'], rec['total_tokens']))
ok('台账里能看见 token 数',
   all(r.get('total_tokens') for r in rec['items']),
   json.dumps(rec['items'][-1], ensure_ascii=False)[:100])

# 4) /ping 也关思考
src = io.open(bridge.__file__, encoding='utf-8').read()
i = src.find("body = {'model': model, 'max_tokens': 1")
ok('连通性测试也关思考', i > 0 and 'thinking' in src[i:i + 160], src[i:i + 120].replace('\n', ' '))

print('\n[SUM] %d 通过 / %d 失败' % (ok_n, fail_n))
sys.exit(1 if fail_n else 0)
