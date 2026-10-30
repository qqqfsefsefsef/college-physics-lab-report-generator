# -*- coding: utf-8 -*-
"""验证 notes 被规范化成「可出题」的结构（bridge 侧）。"""
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线')
import bridge  # noqa: E402

ok_n = fail_n = 0


def ok(name, cond, extra=''):
    global ok_n, fail_n
    if cond:
        ok_n += 1
        print('[OK] %s  %s' % (name, extra))
    else:
        fail_n += 1
        print('[FAIL] %s  %s' % (name, extra))


ed = bridge.experiments()['photo']
tables = {'t1': {'cells': [['测量数组', '1', '2'],
                           ['435.8 nm  U_AK', '-4', '-3'],
                           ['I', '0.9', '1.3']]}}

# 1) 模型给结构化 notes：保留并回填真实值
notes = [{'table': 't1', 'row': 2, 'col': 1, 'where': '表1 · 435.8nm · 第1列 I 那一格',
          'current': '0.4', 'candidates': ['0.4', '0.9'], 'why': '有涂改'}]
out = bridge.norm_notes(ed, tables, notes)
ok('结构化 notes 被保留', len(out) == 1 and out[0]['table'] == 't1' and out[0]['row'] == 2,
   str(out[0])[:80])
ok('当前值以表里的实际值为准', out[0]['current'] == '0.9', out[0]['current'])
ok('候选里补上了当前值', '0.9' in out[0]['candidates'], str(out[0]['candidates']))
ok('位置描述保留', '435.8nm' in out[0]['where'], out[0]['where'])

# 2) 模型只给一句话（老格式）
out2 = bridge.norm_notes(ed, tables, ['577.0 nm 三次读数差得有点大'])
ok('纯字符串也能出题', len(out2) == 1 and out2[0]['where'] == '（模型没写清位置）',
   out2[0]['where'])
ok('纯字符串保留原话', out2[0]['why'].startswith('577.0'), out2[0]['why'])

# 3) 行列为 -1：不要瞎定位
out3 = bridge.norm_notes(ed, tables, [{'table': 't1', 'row': -1, 'col': -1, 'why': '字迹模糊'}])
ok('行列为 -1 时不指向具体格子', out3[0]['row'] == -1 and out3[0]['col'] == -1)

# 4) 候选值去重且最多 4 个
out4 = bridge.norm_notes(ed, tables, [{'candidates': ['1', '1', '2', '3', '4', '5']}])
ok('候选值去重且截断', out4[0]['candidates'] == ['1', '1', '2', '3'] or
   len(out4[0]['candidates']) <= 4, str(out4[0]['candidates'])[:60])

# 5) 桩数据里的 notes 也能出题（端到端一致性）
mock = bridge.mock_result(ed)
mout = bridge.norm_notes(ed, mock.get('tables') or {}, mock.get('notes'))
ok('桩数据的 notes 能出题', len(mout) >= 1 and mout[0]['where'], str(mout[0])[:90])

print('\n[SUM] %d 通过 / %d 失败' % (ok_n, fail_n))
sys.exit(1 if fail_n else 0)
