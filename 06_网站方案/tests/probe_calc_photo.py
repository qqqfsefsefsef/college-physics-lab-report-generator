import json
import os
import sys

HERE = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线'
sys.path.insert(0, HERE)
import bridge  # noqa
import core  # noqa

ed = json.load(open(os.path.join(HERE, 'experiments', 'photo.json'), encoding='utf-8'))
res = bridge.mock_result(ed)
tables = res['tables']
print('t3 rows:', len(tables['t3']['cells']))
for r in tables['t3']['cells']:
    print('  ', r)
calc = core.calc_photo(ed, tables)
print('u0_avg', calc['t3']['u0_avg'])
print('u_s', calc['t3']['u_s'])
print('nu', calc['t3']['nu'])
out = core.calc_photo(ed, tables)['result']
print('result:', json.dumps({k: (round(v, 6) if isinstance(v, float) else v) for k, v in out.items()},
                            ensure_ascii=False))
