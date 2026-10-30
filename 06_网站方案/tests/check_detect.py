# -*- coding: utf-8 -*-
r"""/detect 冒烟测试：桩模式应返回 photo；无 key 真实模式应给明确提示。"""
import base64
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')
B = 'http://127.0.0.1:8732'
IMG = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\tests\fixture.jpg'
b64 = base64.b64encode(open(IMG, 'rb').read()).decode()


def post(path, obj):
    rq = urllib.request.Request(B + path, data=json.dumps(obj).encode(),
                                headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(rq, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


code, body = post('/detect', {'image_b64': b64, 'mime': 'image/jpeg', 'mode': 'mock'})
print('/detect mock ->', code, body.get('ok'), body.get('exp_id'), body.get('name'),
      '| detected=', body.get('detected'))

code, body = post('/detect', {'image_b64': b64, 'mime': 'image/jpeg'})
print('/detect real(no key) ->', code, str(body.get('error'))[:60])

with urllib.request.urlopen(B + '/health', timeout=10) as r:
    h = json.loads(r.read().decode())
print('/health', r.status, h['mode'], 'has_key=', h['has_key'])
