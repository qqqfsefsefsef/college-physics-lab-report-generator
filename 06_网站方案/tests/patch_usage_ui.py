# -*- coding: utf-8 -*-
"""页面显示识别用量（tokens），并在识别失败时把用量也带出来。"""
import io

P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(P, encoding='utf-8').read()
orig = s

# ---------- 1. 工具函数：把 usage 变成一行人能看懂的字 ----------
anchor = "function identify(file, cb) {"
helper = '''function usageLine(u) {
  if (!u || (!u.total_tokens && !u.prompt_tokens)) return '';
  var inTok = u.prompt_tokens || 0, outTok = u.completion_tokens || 0;
  var tot = u.total_tokens || (inTok + outTok);
  return '用量：输入 ' + inTok + ' + 输出 ' + outTok + ' = ' + tot + ' tokens';
}

'''
assert anchor in s
s = s.replace(anchor, helper + anchor, 1)

# ---------- 2. 识别成功：把用量追加到状态行 ----------
old = """      var notes = (j.notes || []).length;
      setRec('识别完成' + (notes ? '，' + notes + ' 处要人工确认' : '，没有发现歧义') +
        ' · 结果会先进核对屏', 'ok');"""
new = """      var notes = (j.notes || []).length;
      var uline = usageLine(j.meta && j.meta.usage);
      setRec('识别完成' + (notes ? '，' + notes + ' 处要人工确认' : '，没有发现歧义') +
        ' · 结果会先进核对屏' + (uline ? '（' + uline + '）' : ''), 'ok');
      STATE.lastUsage = uline;"""
assert old in s
s = s.replace(old, new, 1)

# ---------- 3. 识别失败：也把用量带出来 ----------
old = """        if (j.first_error) msg += '｜第一次：' + String(j.first_error).slice(0, 120);
        setRec('识别失败：' + msg, 'bad');"""
new = """        if (j.first_error) msg += '｜第一次：' + String(j.first_error).slice(0, 120);
        var ul = usageLine((dg && dg.usage) || (j.diag && j.diag.usage));
        if (ul) msg += '｜' + ul + '（这次也花了钱）';
        setRec('识别失败：' + msg, 'bad');"""
assert old in s
s = s.replace(old, new, 1)

# ---------- 4. 结果屏：显示本次总用量（如果桥回传） ----------
old = """function fillResult() {"""
new = """function fillResult() {
  var ubox = document.getElementById('res-usage');"""
assert old in s
s = s.replace(old, new, 1)

# 在 fillResult 的成功分支里写 res-usage（找 fillKpi(STATE.out) 之类调用点）
if 'res-usage' in s:
    old2 = """  var ok = !!(STATE.out && STATE.out.name);"""
    if old2 in s:
        s = s.replace(old2, old2 + """
  if (ubox) {
    var u = STATE.out && STATE.out.usage;
    ubox.textContent = u ? usageLine(u) : (STATE.lastUsage || '');
    ubox.style.display = ubox.textContent ? '' : 'none';
  }""", 1)

# ---------- 5. S7 结果屏加一块占位 ----------
if 'id="res-usage"' not in s:
    old3 = '<div id="res-err"'
    if old3 in s:
        s = s.replace(old3, '<div id="res-usage" class="hint" style="margin:6px 0 2px;display:none"></div>\n    ' + old3, 1)

assert s != orig
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[OK] page patched, %d -> %d chars' % (len(orig), len(s)))
