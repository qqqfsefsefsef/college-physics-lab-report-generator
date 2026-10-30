import sys

sys.stdout.reconfigure(encoding='utf-8')
p = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = open(p, encoding='utf-8').read()
print('chars', len(s))
keys = ['rec-note', 'rec-wrap', 'btn-dl', 'buildReviewFromRec', 'renderReport',
        'useMockRec', 't-review', 'function fillResult', 'payload', 'api_key',
        'STATE.out', 'mode']
for k in keys:
    print('%-22s %d' % (k, s.count(k)))
