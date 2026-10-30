#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
本地桥：把浏览器里上传的照片，转给视觉模型，回一份结构化的表格 JSON。

为什么需要它：
  1) 浏览器直连大模型接口会被 CORS 挡掉；
  2) 密钥不该出现在页面里，也不该写进 localStorage（保持"关了页面就没了"）;
  3) 识别结果必须先过一道 schema，再进闸门，最后交给确定性计算。

启动：
    python 07_流水线/bridge.py                 # 真实模式，读 .env 里的 DEEPSEEK_API_KEY
    python 07_流水线/bridge.py --mock          # 桩模式，不联网，用内置数据回一份结果（跑通链路用）

接口：
    GET  /health                    -> {ok, mode, model, has_key, experiments}
    POST /recognize  {exp_id, image_b64, mime}  -> {exp_id, tables, warnings, meta}
    POST /calc       {exp_id, tables}           -> 直接算一遍（不进项目，给前端即时反馈）
    OPTIONS *                       -> CORS 预检

约定：任何响应里都不回显密钥；日志里密钥一律打码。
"""
import argparse
import base64
import io
import json
import os
import re
import sys
import tempfile
import time
import urllib.request
import urllib.error
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    sys.stdout.reconfigure(errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
EXP_DIR = os.path.join(HERE, 'experiments')
PORT = int(os.environ.get('BRIDGE_PORT', '8732'))
DEFAULT_BASE = 'https://api.deepseek.com/v1'
DEFAULT_MODEL = 'deepseek-v4-flash-vision-exp'


# ---------------------------------------------------------------- 图片规整
class HeicError(Exception):
    pass


HEIC_BRANDS = (b'heic', b'heix', b'hevc', b'hevx', b'mif1', b'msf1', b'avif')


def looks_like_heic(raw):
    head = raw[:64]
    return b'ftyp' in head and any(b in head for b in HEIC_BRANDS)


def heic_to_png(raw):
    """用 Windows 自带的 WIC 解码 HEIC（Pillow 12 不含 HEIF，装不了插件）。

    走「stdin 进 / stdout 出」，全程不碰磁盘——沙箱里写临时文件会 EACCES。
    """
    if os.name != 'nt':
        raise HeicError('这台机器不是 Windows，没有可用的 HEIC 解码器。')
    ps = (
        '$in=[Console]::OpenStandardInput();'
        '$ms=New-Object System.IO.MemoryStream;'
        '$in.CopyTo($ms);$ms.Position=0;'
        'Add-Type -AssemblyName PresentationCore;'
        '$d=[System.Windows.Media.Imaging.BitmapDecoder]::Create('
        '$ms,'
        '[System.Windows.Media.Imaging.BitmapCreateOptions]::None,'
        '[System.Windows.Media.Imaging.BitmapCacheOption]::OnLoad);'
        '$e=New-Object System.Windows.Media.Imaging.PngBitmapEncoder;'
        '$e.Frames.Add([System.Windows.Media.Imaging.BitmapFrame]::Create($d.Frames[0]));'
        '$o=New-Object System.IO.MemoryStream;$e.Save($o);'
        '[Console]::Out.Write([Convert]::ToBase64String($o.ToArray()))'
    )
    try:
        import subprocess
        r = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', ps],
                           input=raw, capture_output=True, timeout=120)
    except Exception as e:
        raise HeicError('HEIC 转码出错：%s' % e)
    if r.returncode != 0 or not r.stdout:
        msg = (r.stderr or b'').decode('utf-8', 'replace').strip()[:300]
        raise HeicError('WIC 解不出这张 HEIC。' + (('（' + msg + '）') if msg else ''))
    try:
        return base64.b64decode(r.stdout.strip())
    except Exception as e:
        raise HeicError('HEIC 转码结果读不出来：%s' % e)


def normalize_image(raw, mime='image/jpeg', max_side=1600, quality=88):
    """把任意输入图片压成模型能吃的 JPEG。返回 (bytes, mime, info)。"""
    from PIL import Image
    import io

    info = {'in_mime': mime, 'in_kb': round(len(raw) / 1024.0, 1)}
    if looks_like_heic(raw):
        raw = heic_to_png(raw)
        info['converted_from'] = 'heic'
    im = Image.open(io.BytesIO(raw))
    im.load()
    info['in_size'] = list(im.size)
    if im.mode not in ('RGB', 'L'):
        im = im.convert('RGB')
    w, h = im.size
    if max(w, h) > max_side:
        k = float(max_side) / max(w, h)
        im = im.resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS)
        info['resized'] = True
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=quality, optimize=True)
    out = buf.getvalue()
    info.update({'out_mime': 'image/jpeg', 'out_size': list(im.size),
                 'out_kb': round(len(out) / 1024.0, 1)})
    return out, 'image/jpeg', info


# ---------------------------------------------------------------- 配置 / 密钥
def load_env():
    """从 07_流水线/.env 读 KEY=VALUE；已存在的环境变量优先。"""
    p = os.path.join(HERE, '.env')
    if not os.path.exists(p):
        return
    with open(p, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def conf():
    return {
        'base_url': os.environ.get('DSH_BASE_URL', DEFAULT_BASE).rstrip('/'),
        'model': os.environ.get('DSH_MODEL', DEFAULT_MODEL),
        'key': os.environ.get('DEEPSEEK_API_KEY', '').strip(),
    }


def mask(key):
    return (key[:6] + '…' + key[-4:]) if len(key) > 12 else '(空)'


# ---------------------------------------------------------------- 实验定义
def experiments():
    out = {}
    if not os.path.isdir(EXP_DIR):
        return out
    for fn in sorted(os.listdir(EXP_DIR)):
        if fn.endswith('.json'):
            try:
                with open(os.path.join(EXP_DIR, fn), 'r', encoding='utf-8') as f:
                    ed = json.load(f)
                out[ed['id']] = ed
            except Exception as e:
                print('[warn] 读不了 %s: %s' % (fn, e))
    return out


KEYWORDS = {
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


def table_brief(ed):
    """把实验定义里的表规格压成一句人话，给模型当提示。
    表定义可能是 list（[{id,caption,rows,cols,unit_note}]）也可能是 dict（{t1:{row_header,...}}）。"""
    ts = ed.get('tables') or {}
    if isinstance(ts, dict):
        items = list(ts.items())
    else:
        items = [((t.get('id') or 't%d' % (i + 1)), t) for i, t in enumerate(ts)]
    lines = []
    for key, t in items:
        rows = t.get('rows') or t.get('row_header') or t.get('shape') or ''
        cols = t.get('cols') or t.get('col_header') or ''
        unit = t.get('unit_note') or ''
        cap = t.get('caption') or ''
        seg = '%s（%s）' % (cap, key) if cap else key
        if rows:
            seg += ' 行：' + rows
        if cols:
            seg += '；列：' + cols
        if unit:
            seg += '；单位：' + unit
        lines.append('- ' + seg)
    return '\n'.join(lines)


PROMPT = """你是一个实验数据转录器。这是一张大学物理实验的原始数据记录页照片。

实验：{name}（{no}）
本实验的三张表按教材排布如下：
{brief}

要求：
1. 只输出 JSON，不要解释，不要 Markdown 代码块。
2. 结构：{{"exp_id":"{eid}","detected_exp":"照片顶部印着的实验名称（照抄，看不清就填空字符串）","tables":{{"t1":{{"cells":[[...]]}},"t2":{{"cells":[[...]]}},"t3":{{"cells":[[...]]}}}},"notes":["..."]}}
2a. **先看照片顶部印的实验名称**。如果它和上面「实验：」写的不是同一个实验，就把实测名称填进 detected_exp，
    并在 notes 里写「照片是《X》，与指定的《Y》不符」，tables 里所有 cells 一律留空、不要硬填。
3. cells 是二维数组，行优先，**只填数字**，不要带单位，不要中文；空位用 null。
4. 每个数字旁边若看不清/被涂改/有歧义，在 notes 里写明位置和你的两个候选值。
5. 不确定就填你最有把握的那个值，**绝对不要自己编造一个"看起来合理"的数**。
"""


DETECT_PROMPT = """你是一个实验报告识别器。这是一张大学物理实验「原始数据记录页」的照片。

请判断它属于下面哪一个实验（只看照片上印的实验名称、表格结构和公式）：
{menu}

只输出 JSON，不要解释、不要代码块：
{{"exp_id":"列表里的 id；判断不了就填空字符串","detected":"照片上印的实验名称，照抄","evidence":"一句话理由"}}
"""


USAGE_LOG = os.path.join(HERE, 'projects', '_debug', 'usage.jsonl')


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
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
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


def _post_with_thinking(req, c):
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


def call_detect(image_b64, mime, c, ed_map):
    menu = '\n'.join('- %s：%s（%s）' % (k, v.get('name'), v.get('no') or '')
                     for k, v in ed_map.items())
    body = {
        'model': c['model'], 'max_tokens': 1200,
        'thinking': {'type': 'disabled'},
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
    payload = _post_with_thinking(req, c)
    msg = ((payload.get('choices') or [{}])[0].get('message') or {})
    text = msg.get('content') or ''
    log_usage('detect', c['model'], payload.get('usage'),
              {'finish_reason': ((payload.get('choices') or [{}])[0]).get('finish_reason'),
               'len_content': len(text), 'len_reasoning': len(msg.get('reasoning_content') or '')})
    return text, (payload.get('usage') or {})


def call_vision(ed, image_b64, mime, c, strict=False):
    """调一次视觉模型。strict=True 时用更硬的「只输出 JSON」提示，用于重试。"""
    text_prompt = PROMPT.format(name=ed.get('name', ''), no=ed.get('no', ''),
                                brief=table_brief(ed), eid=ed['id'])
    if strict:
        text_prompt += ('\n\n【重要】只输出一个 JSON 对象本身，不要解释、不要 markdown 代码块、'
                        '不要任何前后缀。所有数字用阿拉伯数字，不要写单位。')
    body = {
        'model': c['model'],
        'thinking': {'type': 'disabled'},
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
    payload = _post_with_thinking(req, c)
    ch = (payload.get('choices') or [{}])[0]
    msg = ch.get('message') or {}
    text = msg.get('content') or ''
    think = msg.get('reasoning_content') or ''
    diag = {'finish_reason': ch.get('finish_reason'),
            'len_content': len(text), 'len_reasoning': len(think),
            'usage': payload.get('usage') or {}}
    log_usage('recognize:' + str(ed.get('id')), c['model'], diag.get('usage'), diag)
    if not text and think:
        diag['hint'] = ('模型把内容都写进了思考过程（reasoning_content），content 为空；'
                        '本请求已带 thinking=disabled，若仍如此请把 max_tokens 调大')
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


def _balanced(s, i):
    """从 s[i]=='{' 开始，找出配对的右括号位置（跳过字符串里的括号）。"""
    depth, ins, esc = 0, False, False
    for k in range(i, len(s)):
        ch = s[k]
        if ins:
            if esc:
                esc = False
            elif ch == '\\':
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
    t = re.sub(r'^```[a-zA-Z]*\s*', '', t)
    t = re.sub(r'\s*```$', '', t)
    try:
        return json.loads(t)
    except Exception:
        pass
    i = t.find('{')
    if i < 0:
        raise ValueError('模型没有返回 JSON（内容开头：%s）' % t[:160].replace('\n', ' '))
    j = _balanced(t, i)
    if j < 0:
        raise ValueError('模型返回的 JSON 不完整（可能被截断，长度 %d，开头：%s）'
                         % (len(t), t[:160].replace('\n', ' ')))
    return json.loads(t[i:j + 1])


# ---------------------------------------------------------------- 桩数据（--mock）
def mock_result(ed):
    """不联网时用：钨的逸出功用真实读数，另造一个"看不清"的格子演练闸门。"""
    if ed['id'] == 'tungsten':
        t1 = [[23, 23, 24, 24, 25, 26, 26, 28], [43, 44, 44, 45, 46, 48, 48, 50],
              [78, 80, 81, 83, 84, 86, 87, 88], [139, 140, 142, 143, 152, 152, 153, 157],
              [237, 242, 244, 249, 255, 260, 262, 268], [393, 405, 410, 420, 425, 434, 447, 431],
              [645, 664, 666, 682, 694, 707, 725, 728], [1030, 1050, 1071, 1081, 1112, 1129, 1144, 1162]]
        t2 = [['√U_a', 5, 6, 7, 8, 9, 10, 11, 12],
              ['1.88', 1.36, 1.36, 1.38, 1.38, 1.39, 1.41, 1.41, 1.44],
              ['1.92', 1.63, 1.64, 1.64, 1.65, 1.66, 1.68, 1.68, 1.70],
              ['1.96', 1.89, 1.90, 1.91, 1.92, 1.92, 1.93, 1.94, 1.94],
              ['2.00', 2.14, 2.15, 2.15, 2.16, 2.18, 2.18, 2.18, 2.20],
              ['2.04', 2.37, 2.38, 2.39, 2.40, 2.41, 2.42, 2.42, 2.43],
              ['2.08', 2.59, 2.61, 2.61, 2.62, 2.63, 2.63, 2.65, 2.65],
              ['2.12', 2.81, 2.82, 2.82, 2.83, 2.84, 2.85, 2.86, 2.86],
              ['2.16', 3.01, 3.02, 3.03, 3.03, 3.05, 3.05, 3.06, 3.07]]
        t3 = [['T/10³K', 1.88, 1.92, 1.96, 2.00, 2.04, 2.08, 2.12, 2.16],
              ['1/T', 0.53, 0.52, 0.51, 0.50, 0.49, 0.48, 0.47, 0.46],
              ['lg I_s', 1.29, 1.57, 1.85, 2.09, 2.32, 2.55, 2.78, 2.97],
              ['lg(I_s/T²)', 0.75, 1.01, 1.27, 1.50, 1.71, 1.92, 2.12, 2.30]]
        return {'exp_id': ed['id'],
                'tables': {'t1': {'cells': t1}, 't2': {'cells': t2}, 't3': {'cells': t3}},
                'notes': ['【桩】表 1 第 6 行第 8 列（0.725 A / 144 V）看着像 431，'
                          '但和同行 447 不单调，请人工确认。',
                          '【桩】表 2 第 8 行（T = 2.16×10³K）学生写在框线外，已按位置补入。']}
    if ed['id'] == 'young':
        t1 = [['荷重/kg', '增重读数', '减重读数']] + [
            [2.000 + k, v, w] for k, (v, w) in enumerate(zip(
                [10.00, 12.79, 15.57, 18.36, 21.13, 23.92, 26.70, 29.48],
                [10.03, 12.82, 15.60, 18.39, 21.17, 23.95, 26.73, 29.51]))]
        t2 = [['直径 d / mm（6 次）', 0.298, 0.301, 0.299, 0.302, 0.300, 0.301],
              ['千分尺零点 / mm', 0.002]]
        t3 = [['D / m', 1.5000], ['L / m', 1.0000], ['K / m', 0.0750],
              ['千分尺零点 / mm', 0.002], ['g / (m·s⁻²)', 9.794]]
        return {'exp_id': ed['id'],
                'tables': {'t1': {'cells': t1}, 't2': {'cells': t2}, 't3': {'cells': t3}},
                'notes': ['【桩】杨氏模量示例数据：钢丝直径 6 次、加减砝码各 8 次，'
                          '计算结果 Y ≈ 2.02×10¹¹ Pa。']}
    if ed['id'] == 'photo':
        u_ak = [-4, -3, -2, -1, 0, 1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
        i_b = [0.9, 1.3, 1.7, 2.2, 2.9, 9.0, 13.6, 16.9, 19.4, 22.6, 27.0, 30.3, 33.0, 35.3,
               37.0, 39.0, 40.7, 42.3, 43.7, 45.0, 45.9, 46.8]
        i_g = [0.5, 0.1, 0.4, 2.0, 3.3, 13.5, 19.3, 24.9, 30.3, 35.3, 40.8, 45.2, 48.6, 51.4,
               53.8, 56.1, 58.2, 60.0, 61.7, 63.1, 64.4, 66.2]
        t1 = [['435.8 nm / Φ=2 mm'] + u_ak, ['I/(10⁻¹¹A)'] + i_b,
              ['546.1 nm / Φ=4 mm'] + u_ak, ['I/(10⁻¹¹A)'] + i_g]
        t2 = [['波长', 'Φ=2mm', 'Φ=4mm', 'Φ=8mm'],
              ['435.8 nm', 46.8, 173.0, 687.0],
              ['546.1 nm', 18.0, 65.6, 256.8]]
        t3 = [['λ/nm', 365.0, 404.7, 435.8, 546.1, 577.0],
              ['ν/(10¹⁴Hz)', 8.216, 7.410, 6.882, 5.492, 5.196],
              ['U₀（第1次）', -1.490, -0.917, -0.627, -0.192, -0.169],
              ['U₀（第2次）', -1.507, -0.920, -0.640, -0.200, -0.180],
              ['U₀（第3次）', -1.515, -0.927, -0.656, -0.209, -0.176]]
        return {'exp_id': ed['id'], 'tables': {'t1': {'cells': t1}, 't2': {'cells': t2},
                                              't3': {'cells': t3}},
                'notes': ['【桩】表 1 是 435.8 nm/2 mm 与 546.1 nm/4 mm 两组曲线；'
                          '577.0 nm 那一列三次读数差得有点大，已按原始记录保留。']}
    return {'exp_id': ed['id'], 'tables': {}, 'notes': ['【桩】这个实验还没有桩数据。']}


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    server_version = 'dsh-bridge/0.1'

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')

    def _json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        sys.stderr.write('[bridge] %s\n' % (fmt % args))

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        import urllib.parse as _up
        parsed = _up.urlparse(self.path)
        if parsed.path == '/usage':
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            return self._json(read_usage(int((q.get('n') or ['20'])[0] or 20)))
        if parsed.path == '/file':
            return self._file(_up.parse_qs(parsed.query))
        if parsed.path != '/health':
            return self._json({'error': 'not found'}, 404)
        c = conf()
        return self._json({'ok': True, 'mode': 'mock' if self.server.mock else 'real',
                           'model': c['model'], 'base_url': c['base_url'],
                           'has_key': bool(c['key']), 'key_hint': mask(c['key']),
                           'experiments': [{'id': k, 'name': v.get('name'), 'no': v.get('no')}
                                           for k, v in experiments().items()]})

    def do_POST(self):
        path = self.path.split('?')[0]
        try:
            n = int(self.headers.get('Content-Length') or 0)
            req = json.loads(self.rfile.read(n).decode('utf-8')) if n else {}
        except Exception as e:
            return self._json({'error': '请求体不是 JSON: %s' % e}, 400)

        if path == '/detect':
            return self._detect(req)
        if path == '/recognize':
            return self._recognize(req)
        if path == '/ping':
            return self._ping(req)
        if path == '/calc':
            return self._calc(req)
        if path == '/style':
            return self._style(req)
        if path == '/render':
            return self._render(req)
        return self._json({'error': 'not found'}, 404)

    # -------- /ping  真连通性测试：一次 1 token 的调用
    def _ping(self, req):
        c = conf()
        key = (req.get('api_key') or '').strip() or c['key']
        base = ((req.get('base_url') or '').strip() or c['base_url']).rstrip('/')
        model = (req.get('model') or '').strip() or c['model']
        if not key:
            return self._json({'ok': False, 'error': '页面里没填密钥，服务端也没配'})
        body = {'model': model, 'max_tokens': 1, 'thinking': {'type': 'disabled'},
                'messages': [{'role': 'user', 'content': 'ping'}]}
        t0 = time.time()
        try:
            rq = urllib.request.Request(base + '/chat/completions',
                                        data=json.dumps(body).encode('utf-8'),
                                        headers={'Content-Type': 'application/json',
                                                 'Authorization': 'Bearer ' + key},
                                        method='POST')
            with urllib.request.urlopen(rq, timeout=25) as r:
                json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            return self._json({'ok': False, 'error': 'HTTP %s %s' % (e.code, e.read().decode('utf-8', 'replace')[:200])})
        except Exception as e:
            return self._json({'ok': False, 'error': str(e)[:200]})
        return self._json({'ok': True, 'ms': int((time.time() - t0) * 1000), 'model': model})

    # -------- /style  读用户以前的报告，抽一张「他/她怎么写」的风格卡
    def _style(self, req):
        b64 = (req.get('docx_b64') or '').strip()
        if not b64:
            return self._json({'error': '没有收到作业文件（.docx）'}, 400)
        sys.path.insert(0, HERE)
        try:
            import style as style_mod
        except Exception as e:
            return self._json({'error': '风格模块加载失败: %s' % e}, 500)
        raw = base64.b64decode(b64.split(',')[-1])
        if len(raw) < 4096:
            return self._json({'error': '这个文件太小了，不像一份报告（请传 .docx）'}, 400)
        if raw[:2] != b'PK':
            return self._json({'error': '这不是 .docx（可能传了 .doc/.pdf）。用 Word「另存为」成 .docx 再传。'}, 400)
        cache = os.path.join(HERE, 'projects', '_hw')
        os.makedirs(cache, exist_ok=True)
        tag = time.strftime('%Y%m%d-%H%M%S')
        path = os.path.join(cache, 'hw-%s.docx' % tag)
        with open(path, 'wb') as f:
            f.write(raw)
        try:
            card = style_mod.card(path)
        except Exception as e:
            return self._json({'error': '这份作业读不动：%s' % e}, 400)
        card['path'] = path
        json.dump(card, open(os.path.join(cache, 'hw-%s.json' % tag), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        return self._json(card)

    # -------- /detect  先认这是哪个实验
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

    # -------- /recognize
    def _recognize(self, req):
        exps = experiments()
        eid = (req.get('exp_id') or '').strip()
        if eid not in exps:
            return self._json({'error': '未知实验：%s' % eid, 'known': sorted(exps)}, 400)
        ed = exps[eid]
        img = req.get('image_b64') or ''
        mime = req.get('mime') or 'image/jpeg'
        if not img:
            return self._json({'error': '没有收到图片'}, 400)

        # 不管前端传什么，先把图片规整成模型能吃的 JPEG：
        # 手机原图多是 HEIC（Pillow 不认），另外 3~4 千万像素也没必要整张发过去。
        try:
            raw = base64.b64decode(img)
        except Exception:
            return self._json({'error': '图片不是合法的 base64'}, 400)
        try:
            img, mime, imeta = normalize_image(raw, mime)
        except HeicError as e:
            return self._json({'error': str(e), 'hint': 'HEIC 转码失败：Windows 上可用「照片」另存为 JPG 后重传。'}, 415)
        except Exception as e:
            return self._json({'error': '这张图读不出来（%s）。请传 JPG / PNG 的照片。' % e}, 415)
        img = base64.b64encode(img).decode('ascii')

        if self.server.mock or req.get('mode') == 'mock':
            res = mock_result(ed)
            res['meta'] = {'mode': 'mock', 'model': None, 'usage': {}, 'image': imeta}
            return self._json(res)

        c = conf()
        # 页面里临时填的密钥优先（只在内存里，用完即弃），服务端配置作兜底
        key = (req.get('api_key') or '').strip() or c['key']
        base = (req.get('base_url') or '').strip() or c['base_url']
        model = (req.get('model') or '').strip() or c['model']
        if not key:
            return self._json({'error': '还没有密钥：在首页「接入自己的 API」里填一次（只在内存里，关页面就没了），'
                                       '或让服务端配好 DEEPSEEK_API_KEY。'}, 400)
        c = {'key': key, 'base_url': base.rstrip('/'), 'model': model}
        diag = {}
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
                                            'retried': True}}, 502)
        res['exp_id'] = eid
        res.setdefault('notes', [])
        det = (res.get('detected_exp') or '').strip()
        sug = match_exp(det) if det else None
        if det and sug and sug != eid:
            return self._json({
                'error': '这张照片印的是《%s》，不是你现在选的《%s》。' % (det, ed.get('name')),
                'mismatch': True, 'detected': det, 'suggest': sug,
                'suggest_name': experiments()[sug].get('name'),
            }, 409)
        res['meta'] = {'mode': 'real', 'model': c['model'], 'usage': usage,
                       'bytes': len(img) * 3 // 4, 'image': imeta,
                       'diag': diag or {}}
        return self._json(res)

    # -------- /calc
    def _calc(self, req):
        exps = experiments()
        eid = (req.get('exp_id') or '').strip()
        if eid not in exps:
            return self._json({'error': '未知实验：%s' % eid}, 400)
        sys.path.insert(0, HERE)
        try:
            import core  # 复用 07_流水线 里的确定性计算
        except Exception as e:
            return self._json({'error': 'core 加载失败: %s' % e}, 500)
        ed = exps[eid]
        fn = getattr(core, 'calc_' + eid, None)
        if not fn:
            return self._json({'error': 'core 里没有 calc_%s' % eid}, 500)
        try:
            # 两种数据约定都兼容：calc_* 里既可以读 data['t1']，也可以读 data['tables']['t1']
            tables = req.get('tables') or {}
            data = dict(tables)
            data['tables'] = tables
            calc = fn(ed, data)
        except Exception as e:
            return self._json({'error': '计算失败：%s' % e}, 500)
        return self._json({'ok': True, 'result': calc.get('result'), 'provenance': calc.get('provenance')})

    # -------- /render   表格 + 实验定义 -> docx
    @staticmethod
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

    def _render(self, req):
        if self.tables_empty((req or {}).get('tables')):
            return self._json({'error': '还没有可用的数据表：这张照片没认出数字（可能拍虚了、反光，'
                                       '或者不是这个实验的记录页）。回到上传屏换一张清楚的照片，'
                                       '只拍表格区域、正对着拍。'}, 400)
        exps = experiments()
        eid = (req.get('exp_id') or '').strip()
        if eid not in exps:
            return self._json({'error': '未知实验：%s' % eid}, 400)
        ed = exps[eid]
        sys.path.insert(0, HERE)
        try:
            import core
            import ir
            import render_docx
        except Exception as e:
            return self._json({'error': '渲染模块加载失败: %s' % e}, 500)
        fn = getattr(core, 'calc_' + eid, None)
        if not fn:
            return self._json({'error': 'core 里没有 calc_%s' % eid}, 500)

        tables = req.get('tables') or {}
        prov = req.get('provenance') or {}
        if not prov:
            prov = {'source': 'mock'} if self.server.mock else {'source': 'photo'}
        tables = core.normalize_input(ed, tables)
        data = dict(tables)
        data['tables'] = tables
        data['provenance'] = prov
        try:
            calc = fn(ed, data)
        except Exception as e:
            return self._json({'error': '计算失败：%s' % e}, 500)

        stamp = time.strftime('%Y%m%d-%H%M%S')
        proj = os.path.join(HERE, 'projects', 'web-%s-%s' % (eid, stamp))
        outdir = os.path.join(proj, 'out')
        os.makedirs(outdir, exist_ok=True)
        json.dump(data, open(os.path.join(proj, 'data.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        json.dump(calc, open(os.path.join(proj, 'calc.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)

        md_path = ed.get('content') or ''
        if md_path and not os.path.isabs(md_path):
            md_path = os.path.join(WORK, md_path)
        if not md_path or not os.path.exists(md_path):
            return self._json({'error': '这个实验还缺正文（%s）' % (ed.get('content') or '未填写')}, 500)

        # 学习通截图：有就落盘进项目 source/，渲染时贴进最后的 1×1 框
        assets = {}
        shot_b64 = (req.get('shot_b64') or '').strip()
        if shot_b64:
            try:
                raw = base64.b64decode(shot_b64.split(',')[-1])
                img, mime, info = normalize_image(raw, req.get('shot_mime') or '', max_side=1600, quality=90)
                shotdir = os.path.join(proj, 'source')
                os.makedirs(shotdir, exist_ok=True)
                shot_path = os.path.join(shotdir, 'shot.jpg')
                with open(shot_path, 'wb') as f:
                    f.write(img)
                assets['shot'] = shot_path
                json.dump(info, open(os.path.join(shotdir, 'shot.json'), 'w', encoding='utf-8'),
                          ensure_ascii=False, indent=1)
            except Exception as e:
                return self._json({'error': '学习通截图读不了：%s（换一张 PNG/JPG 截图试试）' % e}, 400)

        try:
            blocks = ir.build(ed, calc, md_path, assets=assets)
            json.dump(blocks, open(os.path.join(proj, 'blocks.json'), 'w', encoding='utf-8'),
                      ensure_ascii=False, indent=1)
            name = (req.get('title') or ed.get('name') or eid) + '.docx'
            out = os.path.join(outdir, name)
            render_docx.render(blocks, out, ed.get('name'),
                           footer=ed.get('footer') or ed.get('name'))
        except Exception as e:
            return self._json({'error': '排版失败：%s' % e}, 500)

        rel = os.path.relpath(out, os.path.join(HERE, 'projects')).replace('\\', '/')
        return self._json({'ok': True, 'name': name, 'bytes': os.path.getsize(out),
                           'url': '/file?path=' + urllib.parse.quote(rel),
                           'project': os.path.basename(proj),
                           'result': calc.get('result'),
                           'kpi': ed.get('kpi')})

    # -------- /file?path=web-xxx/out/yyy.docx   只能取 projects 下的文件
    def _file(self, query):
        import urllib.parse as _up
        rel = _up.unquote((query.get('path') or [''])[0])
        root = os.path.join(HERE, 'projects')
        target = os.path.abspath(os.path.join(root, rel))
        if not target.startswith(os.path.abspath(root)) or not os.path.isfile(target):
            return self._json({'error': '找不到这个文件'}, 404)
        with open(target, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument'
                                        '.wordprocessingml.document')
        self.send_header('Content-Disposition',
                         "attachment; filename*=UTF-8''" + urllib.parse.quote(os.path.basename(target)))
        self.send_header('Content-Length', str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mock', action='store_true', help='不联网，返回桩数据（验证链路用）')
    ap.add_argument('--port', type=int, default=PORT)
    args = ap.parse_args()
    load_env()
    c = conf()
    srv = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    srv.mock = args.mock
    print('[bridge] http://127.0.0.1:%d  mode=%s  model=%s  key=%s'
          % (args.port, 'mock' if args.mock else 'real', c['model'], mask(c['key'])))
    print('[bridge] 实验：%s' % ', '.join(experiments()) or '(无)')
    print('[bridge] Ctrl+C 停止')
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\n[bridge] bye')


if __name__ == '__main__':
    main()
