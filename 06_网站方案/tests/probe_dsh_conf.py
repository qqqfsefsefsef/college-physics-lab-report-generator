import os
import re

H = r'C:\Users\lidey\.dsh'

p = os.path.join(H, 'profiles', 'desktop', '.dsh-market', 'discovery-compatibility-v1.json')
try:
    t = open(p, encoding='utf-8', errors='ignore').read()
    for m in re.findall(r'sk-[A-Za-z0-9_\-]{16,}', t)[:3]:
        print('market hit:', m[:8] + '...' + m[-6:], 'len', len(m))
except Exception as e:
    print('read fail', e)

print()
base = os.path.join(H, 'profiles')
pat = re.compile(r'"(?:apiKey|api_key|baseUrl|base_url|model)"\s*:\s*"([^"]{4,90})"')
for root, dirs, files in os.walk(base):
    depth = root.count(os.sep) - base.count(os.sep)
    if depth > 2:
        dirs[:] = []
        continue
    for fn in files:
        low = fn.lower()
        if not ('config' in low or 'auth' in low or 'setting' in low or low.endswith('.json')):
            continue
        fpath = os.path.join(root, fn)
        try:
            txt = open(fpath, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        found = pat.findall(txt)
        if found:
            masked = [(x[:6] + '...' if len(x) > 12 else x) for x in found]
            print(os.path.relpath(fpath, H), '->', masked[:8])
