# -*- coding: utf-8 -*-
r"""把核对屏说人话：实验对不上给一键切换；问题卡改「按这个来」；结果失败要说清楚。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(P, encoding='utf-8').read()
orig = len(s)
n = 0


def rep(old, new, tag):
    global s, n
    assert s.count(old) == 1, '未命中：%s（出现 %d 次）' % (tag, s.count(old))
    s = s.replace(old, new)
    n += 1
    print('[OK]', tag)


# ---------------- 1) 标题与说明改成大白话
rep("    <h2>先对一遍数据</h2>\n"
    "    <p class=\"lead\">左边是可改的表格，右边是我发现的问题。改完点「确认」才会开始生成——生成后的数字只认这张表。</p>",
    "    <h2>第 3 步 · 看一眼这些数字对不对</h2>\n"
    "    <p class=\"lead\">下面这些数字是从你刚上传的照片里认出来的。<b>拿它和你纸上的表格对一遍</b>："
    "哪个格子错了就直接点它改过来。数字对了，点最下面那个按钮，就开始生成报告——"
    "<b>报告里的数字只认这张表</b>，它不会再去看照片。</p>\n"
    "    <div id=\"mm\" class=\"mm\" style=\"display:none\"></div>",
    'S5 标题与说明')

# ---------------- 2) 右栏改成「需要你确认的地方」
rep("      <div>\n        <div class=\"chat\" id=\"chat\"></div>",
    "      <div>\n"
    "        <div class=\"rtitle\">需要你确认的 <span id=\"issue-n\">0</span> 处</div>\n"
    "        <div class=\"rsub\">每处点一次「按这个来」就行；没有把握的，去左边改数字。</div>\n"
    "        <div class=\"chat\" id=\"chat\"></div>",
    'S5 右栏标题')

rep("        <button class=\"btn pri\" id=\"btn-ok\" onclick=\"go('s-gen')\" disabled>数据确认无误</button>\n"
    "        <div class=\"hint\" id=\"ok-hint\">把上面两条问题各点一次「知道了」才能继续。</div>",
    "        <button class=\"btn pri\" id=\"btn-ok\" onclick=\"go('s-gen')\" disabled>数字都对，生成报告</button>\n"
    "        <div class=\"hint\" id=\"ok-hint\">先看右边：有几处要你点一下确认。</div>",
    'S5 主按钮文案')

# ---------------- 3) 「知道了」→「按这个来」
rep("    b.textContent = '知道了';", "    b.textContent = '按这个来';", '确认按钮文案')
rep("      b.textContent = '已确认';", "      b.textContent = '已确认 ✓';", '已确认文案')
rep("        $('ok-hint').textContent = '都确认过了，可以开始生成。';",
    "        $('ok-hint').textContent = '都确认了，点上面这个按钮生成报告。';", '提示-全确认')
rep("        $('ok-hint').textContent = '还剩 ' + left + ' 条要确认。';",
    "        $('ok-hint').textContent = '还剩 ' + left + ' 处要点一下。';", '提示-还剩')

# ---------------- 4) 问题数显示 + 空表提示
rep("""  var chat = $('chat');
  chat.innerHTML = '';
  STATE.reviewed = {};""",
    """  var ic = $('issue-n');
  if (ic) ic.textContent = ISSUES.length;
  var chat = $('chat');
  chat.innerHTML = '';
  STATE.reviewed = {};""",
    '问题数回填')

rep("  wrap.innerHTML = html || '<div class=\"hint\">这张照片没有识别出表格。</div>';",
    "  wrap.innerHTML = html || ('<div class=\"empty\">这张照片里没认出表格。<br>"
    "建议只拍表格那一片、正对着拍、别反光；也可能是拍错了实验。' +\n"
    "    '<div style=\"margin-top:10px\"><button class=\"btn\" onclick=\"go(\\'s-upload\\')\">换一张照片</button></div></div>');",
    '空表提示')

# ---------------- 5) 实验对不上：一键切换
rep("""      if (j.error) {
        var msg = String(j.error).replace(/^识别失败：/, '');""",
    """      if (j.mismatch) { showMismatch(j); return cb(false); }
      if (j.error) {
        var msg = String(j.error).replace(/^识别失败：/, '');""",
    'identify 接 mismatch')

rep("function identify(file, cb) {",
    """function showMismatch(j) {
  STATE.pendingExp = j.suggest;
  STATE.pendingName = j.suggest_name || j.detected;
  var mm = $('mm');
  mm.style.display = 'block';
  mm.innerHTML = '<b>这张照片不是你现在选的实验。</b><br>照片上印的是《' + esc(j.detected) +
    '》，你选的是《' + esc(STATE.exp) + '》。' +
    '<div style="margin-top:10px"><button class="btn pri sm" onclick="switchExp()">切成《' +
    esc(STATE.pendingName) + '》再认一次</button></div>';
  setRec('实验对不上：照片是《' + esc(j.detected) + '》', 'bad');
}

function switchExp() {
  if (!STATE.pendingExp) return;
  STATE.exp = STATE.pendingName;
  STATE.expId = STATE.pendingExp;
  var sel = $('exp-sel');
  if (sel) { sel.value = STATE.pendingName; }
  $('mm').style.display = 'none';
  STATE.pendingExp = null;
  if (!STATE.lastFile) { go('s-upload'); return; }
  toast('已切成《' + STATE.exp + '》，正在重新认这张照片…');
  identify(STATE.lastFile, function (ok, j) { if (ok) go('s-review'); });
}

function identify(file, cb) {
  STATE.lastFile = file;""",
    '加 showMismatch/switchExp')

# ---------------- 6) 结果页：失败要说明白，成功要显眼
rep("      <div class=\"kpi\"><div class=\"v num\" id=\"k-y\">—</div><div class=\"k\">杨氏模量 Y / Pa</div></div>",
    "      <div class=\"kpi\"><div class=\"v num\" id=\"k-y\">—</div><div class=\"k\">主结果</div></div>",
    'KPI1 标题')
rep("      <div class=\"kpi\"><div class=\"v num\" id=\"k-u\">—</div><div class=\"k\">相对不确定度 u(Y)/Y</div></div>",
    "      <div class=\"kpi\"><div class=\"v num\" id=\"k-u\">—</div><div class=\"k\">与公认值的相对误差</div></div>",
    'KPI2 标题')
rep("      <div class=\"kpi\"><div class=\"v num\" id=\"k-e\">—</div><div class=\"k\">与公认值 2.0×10¹¹ 的偏差</div></div>",
    "      <div class=\"kpi\"><div class=\"v num\" id=\"k-e\">—</div><div class=\"k\">不确定度</div></div>",
    'KPI3 标题')
rep("    <h2>报告已生成</h2>", "    <h2 id=\"res-h\">报告已生成</h2>", '结果标题加 id')
rep("    <div class=\"card\">\n      <div class=\"row\" style=\"gap:10px;flex-wrap:wrap\">",
    "    <div id=\"res-err\" class=\"mm\" style=\"display:none;margin-bottom:12px\"></div>\n"
    "    <div class=\"card\">\n      <div class=\"row\" style=\"gap:10px;flex-wrap:wrap\">",
    '结果页错误位')

rep("""  } else {
    var r = compute();
    $('k-y').textContent = (r.Y / 1e11).toFixed(3) + '×10¹¹';
    $('k-u').textContent = r.rel.toFixed(2) + '%';
    $('k-e').textContent = (r.Y >= 2e11 ? '+' : '−') + Math.abs((r.Y - 2e11) / 2e11 * 100).toFixed(2) + '%';
    if (ks.length >= 3) {
      ks[0].textContent = '杨氏模量 Y / Pa';
      ks[1].textContent = '相对不确定度 u(Y)/Y';
      ks[2].textContent = '与公认值 2.0×10¹¹ 的偏差';
    }
    dl.textContent = '下载报告';
    dl.onclick = function () { toast('演示环境：正式版这里直接下载' + fmtList() + '文件'); };
  }""",
    """  } else {
    var err = STATE.outErr || '这次没有生成成功。';
    $('k-y').textContent = '—';
    $('k-u').textContent = '—';
    $('k-e').textContent = '—';
    if (ks.length >= 3) {
      ks[0].textContent = '主结果';
      ks[1].textContent = '与公认值的相对误差';
      ks[2].textContent = '不确定度';
    }
    $('res-h').textContent = '没有生成成功';
    var box = $('res-err');
    if (box) {
      box.style.display = 'block';
      box.innerHTML = '<b>原因：</b>' + esc(err) +
        '<div class="hint" style="margin-top:6px">最常见的就是这张照片没认出数字（拍虚、反光、只拍到一部分），' +
        '或者选的实验和照片不是同一个。</div>' +
        '<div style="margin-top:10px"><button class="btn pri sm" onclick="go(\\'s-review\\')">回去核对数字</button> ' +
        '<button class="btn sm" onclick="go(\\'s-upload\\')">换一张照片</button></div>';
    }
    dl.textContent = '报告还没生成';
    dl.onclick = function () { toast('先回去把数据弄对，再生成一次'); };
  }""",
    '结果失败态')

rep("""    } else {
      STATE.out = null;
      toast('生成失败：' + ((j && j.error) || '不知道原因'));
    }""",
    """    } else {
      STATE.out = null;
      STATE.outErr = (j && j.error) || '不知道原因';
      toast('生成失败：' + STATE.outErr);
    }""",
    'renderReport 记下失败原因')

rep("""  }).catch(function () {
    STATE.out = null;
    toast('识别桥没启动，先运行 启动.ps1');
    go('s-result');
  });""",
    """  }).catch(function () {
    STATE.out = null;
    STATE.outErr = '识别桥没在跑（生成服务连不上），先运行「启动.ps1」。';
    toast(STATE.outErr);
    go('s-result');
  });""",
    'renderReport 掉线原因')

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[DONE] %d -> %d 字符，%d 处' % (orig, len(s), n))
