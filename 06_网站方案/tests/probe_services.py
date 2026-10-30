import json
import urllib.request

PAGE = 'http://127.0.0.1:8731/prototype_v2.html'
HEALTH = 'http://127.0.0.1:8732/health'

try:
    with urllib.request.urlopen(PAGE, timeout=5) as r:
        body = r.read()
        print(PAGE, r.status, len(body))
        t = body.decode('utf-8', 'replace')
        for k in ('eidForExp', 'BRIDGE_EXPS', '/ping', 'supportedNames'):
            print('   ', k, '=', k in t)
except Exception as e:
    print(PAGE, 'FAIL', e)

try:
    with urllib.request.urlopen(HEALTH, timeout=5) as r:
        j = json.loads(r.read())
        print(HEALTH, r.status, 'mode=', j['mode'], 'has_key=', j['has_key'])
        print('    experiments =', [e['name'] for e in j['experiments']])
except Exception as e:
    print(HEALTH, 'FAIL', e)
