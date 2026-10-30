# -*- coding: utf-8 -*-
"""P0 前端：结果页 KPI 改成按实验定义驱动（不再写死光电效应）。
顺带给 bridge 的杨氏桩数据补上「千分尺零点」一行。
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
W = r'C:\Users\lidey\Desktop\实验报告制作沙盒'
P = W + r'\06_网站方案\prototype_v2.html'
BP = W + r'\07_流水线\bridge.py'

# ---------------------------------------------------------------- bridge 桩
b = io.open(BP, encoding='utf-8').read()
old = ("        t2 = [['直径 d / mm（6 次）', 0.298, 0.301, 0.299, 0.302, 0.300, 0.301]]")
new = ("        t2 = [['直径 d / mm（6 次）', 0.298, 0.301, 0.299, 0.302, 0.300, 0.301],\n"
       "              ['千分尺零点 / mm', 0.002]]")
if b.count(old) == 1:
    b = b.replace(old, new)
    io.open(BP, 'w', encoding='utf-8', newline='\n').write(b)
    print('[OK] bridge 桩数据补零点行')
else:
    print('[SKIP] bridge 桩数据（已改过）')

# ---------------------------------------------------------------- 前端
s = io.open(P, encoding='utf-8').read()

# 1) renderReport 里 STATE.out = j 已经是整包响应，kpi 自动带上，无需改动
print('[OK] STATE.out 存的是整个响应，kpi 自动可用')

# 2) 插入 kpiText / fillKpi
if 'function fillKpi' not in s:
    helpers = '''function kpiText(spec, o) {
  if (!spec || !o) return '—';
  var v = o[spec.key];
  if (v === undefined || v === null || isNaN(v)) return '—';
  var x = v * (spec.scale || 1);
  var d = (spec.digits === undefined) ? 3 : spec.digits;
  var sign = (x < 0) ? '−' : (spec.signed ? '+' : '');
  return sign + Math.abs(x).toFixed(d) + (spec.suffix || '');
}

function fillKpi(o) {
  var ks = document.querySelectorAll('#s-result .kpi .k');
  var vs = document.querySelectorAll('#s-result .kpi .v');
  var spec = (STATE.out && STATE.out.kpi) || [];
  for (var i = 0; i < vs.length; i++) {
    if (spec[i] && o) {
      vs[i].textContent = kpiText(spec[i], o);
      if (ks[i]) ks[i].textContent = spec[i].label;
    } else {
      vs[i].textContent = '—';
      if (ks[i]) ks[i].textContent = ['主结果', '与公认值的相对误差', '不确定度'][i] || '';
    }
  }
}

'''
    anchor = 'function fillResult() {'
    assert s.count(anchor) == 1
    s = s.replace(anchor, helpers + anchor)
    print('[OK] 插入 kpiText / fillKpi')

# 3) 替换 fillResult 里的写死逻辑
old_success = """    var o = STATE.out.result;
    $('k-y').textContent = (o.h * 1e34).toFixed(3);
    $('k-u').textContent = (o.rel_err_pct >= 0 ? '+' : '−') + Math.abs(o.rel_err_pct).toFixed(2) + '%';
    $('k-e').textContent = (o.u_h * 1e34).toFixed(3);
    if (ks.length >= 3) {
      ks[0].textContent = '普朗克常量 h / 10⁻³⁴ J·s';
      ks[1].textContent = '与公认值 6.626 的相对误差';
      ks[2].textContent = '不确定度 u(h) / 10⁻³⁴ J·s';
    }"""
new_success = """    fillKpi(STATE.out.result);"""
if s.count(old_success) == 1:
    s = s.replace(old_success, new_success)
    print('[OK] fillResult 成功分支改成 fillKpi()')
else:
    print('[SKIP] fillResult 成功分支（已改过）')

old_fail = """    $('k-y').textContent = '—';
    $('k-u').textContent = '—';
    $('k-e').textContent = '—';
    if (ks.length >= 3) {
      ks[0].textContent = '主结果';
      ks[1].textContent = '与公认值的相对误差';
      ks[2].textContent = '不确定度';
    }"""
new_fail = """    fillKpi(null);"""
if s.count(old_fail) == 1:
    s = s.replace(old_fail, new_fail)
    print('[OK] fillResult 失败分支改成 fillKpi(null)')
else:
    print('[SKIP] fillResult 失败分支（已改过）')

# 4) ks 变量已不需要，去掉以免 lint 抱怨（保留也无害，这里只是清掉声明）
s = s.replace("  var ks = document.querySelectorAll('#s-result .kpi .k');\n  var dl = $('btn-dl');",
              "  var dl = $('btn-dl');")

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[DONE] 页面字数', len(s))
