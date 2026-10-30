# -*- coding: utf-8 -*-
r"""验证新 bridge：/health、/render 空表拦截、mismatch 判定函数。"""
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')
B = 'http://127.0.0.1:8732'


def post(path, obj):
    req = urllib.request.Request(B + path, data=json.dumps(obj).encode(),
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


with urllib.request.urlopen(B + '/health', timeout=10) as r:
    h = json.loads(r.read().decode())
print('/health', r.status, h['mode'], 'exps=', [e['id'] for e in h['experiments']])

code, body = post('/render', {'exp_id': 'photo', 'tables': {'t1': {'cells': [[None, None]]}}})
print('/render 空表 ->', code, str(body.get('error'))[:80])

code, body = post('/render', {'exp_id': 'photo', 'tables': {}})
print('/render 无表 ->', code, str(body.get('error'))[:60])

sys.path.insert(0, r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线')
import bridge  # noqa: E402
for name in ['光电效应的研究', '实验 47 光电效应的研究', '钨的逸出功测定', '用静态拉伸法测金属丝的杨氏弹性模量', '霍尔效应', '']:
    print('match_exp(%r) = %r' % (name, bridge.match_exp(name)))
