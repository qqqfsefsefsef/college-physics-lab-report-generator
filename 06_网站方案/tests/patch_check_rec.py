# -*- coding: utf-8 -*-
r"""更新 check_rec.js：无文件时不再回落示例数字，而是明确报失败。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\tests\check_rec.js'
s = io.open(P, encoding='utf-8').read()

old = """/* 没有 docx 时回落到示例数字 */
api.STATE.out = null;
api.fillResult();
ok('无文件时回落示例 Y', /×10¹¹$/.test(document.getElementById('k-y').textContent),
  document.getElementById('k-y').textContent);
ok('KPI 标题回落杨氏模量', kpiLabels[0].textContent.indexOf('杨氏模量') === 0, kpiLabels[0].textContent);"""

new = """/* 没有 docx 时：说清楚为什么没生成，不再假装有结果 */
api.STATE.out = null;
api.STATE.outErr = '还没有可用的数据表：这张照片没认出数字';
api.fillResult();
ok('无文件时 KPI 显示占位', document.getElementById('k-y').textContent === '—',
  document.getElementById('k-y').textContent);
ok('标题改成「没有生成成功」', document.getElementById('res-h').textContent === '没有生成成功',
  document.getElementById('res-h').textContent);
ok('错误卡显示原因并给出退路',
  /没认出数字/.test(document.getElementById('res-err').innerHTML) &&
  /回去核对数字/.test(document.getElementById('res-err').innerHTML),
  document.getElementById('res-err').innerHTML.slice(0, 60));
ok('下载按钮改成「报告还没生成」', document.getElementById('btn-dl').textContent === '报告还没生成',
  document.getElementById('btn-dl').textContent);"""

assert s.count(old) == 1, '回落断言未命中'
s = s.replace(old, new)
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[OK] check_rec.js 已更新', len(s))
