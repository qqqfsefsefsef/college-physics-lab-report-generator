# -*- coding: utf-8 -*-
r"""把这一轮加的功能回填到恢复出来的页面里（每处都校验命中次数）。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(P, encoding='utf-8').read()
orig = len(s)

PATCHES = []

# 1) S5：识别结果区
PATCHES.append((
    '      <div>\n'
    '        <div class="tablewrap">\n'
    '          <table class="grid" id="t-review">',
    '      <div>\n'
    '        <div id="rec-note" class="hint" style="display:none;margin-bottom:8px"></div>\n'
    '        <div id="rec-wrap" style="display:none"></div>\n'
    '        <div class="tablewrap">\n'
    '          <table class="grid" id="t-review">'))

# 2) 结果屏下载按钮加 id
PATCHES.append((
    '<button class="btn pri" onclick="toast(\'演示环境：正式版这里直接下载\' + fmtList() + \'文件\')">下载报告</button>',
    '<button class="btn pri" id="btn-dl" onclick="toast(\'演示环境：正式版这里直接下载\' + fmtList() + \'文件\')">下载报告</button>'))

# 3) buildReview 顶部改走识别结果
PATCHES.append((
    "function buildReview() {\n  var r = compute(), body = $('t-review-body');",
    "function buildReview() {\n"
    "  if (STATE.rec && STATE.rec.tables) { buildReviewFromRec(); return; }\n"
    "  var r = compute(), body = $('t-review-body');"))

# 4) 新函数：核对屏渲染 + 真出 docx
HELPERS = '''/* ---------- S5 用真实识别结果核对 ---------- */
function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>]/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c];
  });
}

function recTableHtml(tb) {
  var rows = (tb && tb.cells) || [], h = '', ri, ci, r, c;
  if (!rows.length) return '';
  h = '<div class="tablewrap" style="margin-bottom:10px"><table class="grid">';
  for (ri = 0; ri < rows.length; ri++) {
    r = rows[ri];
    h += '<tr>';
    for (ci = 0; ci < r.length; ci++) {
      c = esc(r[ci]);
      h += (ri === 0 ? '<th>' + c + '</th>' : '<td class="num">' + c + '</td>');
    }
    h += '</tr>';
  }
  return h + '</table></div>';
}

function buildReviewFromRec() {
  var rec = STATE.rec, notes = rec.notes || [], i;
  ISSUES = notes.map(function (t, k) { return { id: 'n' + k, text: esc(t) }; });

  $('t-review').style.display = 'none';
  var wrap = $('rec-wrap');
  wrap.style.display = 'block';
  var html = '';
  ['t1', 't2', 't3'].forEach(function (k) {
    if (rec.tables[k]) html += recTableHtml(rec.tables[k]);
  });
  wrap.innerHTML = html || '<div class="hint">这张照片没有识别出表格。</div>';

  var img = (rec.meta && rec.meta.image) || {};
  var note = $('rec-note');
  note.style.display = 'block';
  note.textContent = (img.converted_from === 'heic' ? '照片已自动转码 HEIC → JPEG：' : '已识别：') +
    (img.out_size || []).join('×') + '，' + (img.out_kb || '?') + ' KB（原始 ' +
    (img.in_kb || '?') + ' KB）';

  var chat = $('chat');
  chat.innerHTML = '';
  STATE.reviewed = {};
  for (i = 0; i < ISSUES.length; i++) addMsg('bot', ISSUES[i].text, ISSUES[i].id);
  $('conflict').innerHTML = '';
  if (!ISSUES.length) {
    $('btn-ok').disabled = false;
    $('ok-hint').textContent = '识别没有发现疑点，可以直接生成。';
  } else {
    $('btn-ok').disabled = true;
    $('ok-hint').textContent = '把上面 ' + ISSUES.length + ' 条各点一次「知道了」才能继续。';
  }
}

/* ---------- S6 生成（真调识别桥出 docx） ---------- */
function renderReport() {
  var eid = eidForExp(STATE.exp);
  $('gen-step').textContent = '正在排版生成 docx…';
  var prov = ((STATE.rec.meta || {}).mode === 'mock') ? { source: 'mock' } : { source: 'photo' };
  fetch(BRIDGE + '/render', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ exp_id: eid, tables: STATE.rec.tables, provenance: prov })
  }).then(function (r) { return r.json(); }).then(function (j) {
    if (j && j.ok) {
      STATE.out = j;
      toast('报告已生成：' + j.name);
    } else {
      STATE.out = null;
      toast('生成失败：' + ((j && j.error) || '不知道原因'));
    }
    go('s-result');
  }).catch(function () {
    STATE.out = null;
    toast('识别桥没启动，先运行 启动.ps1');
    go('s-result');
  });
}

/* ---------- S6 生成 ---------- */'''
PATCHES.append(('/* ---------- S6 生成 ---------- */', HELPERS))

# 5) 生成到 100% 时真的调桥
PATCHES.append((
    "    if (p >= 100) {\n"
    "      clearInterval(GEN_TIMER);\n"
    "      setTimeout(function () { go('s-result'); }, 450);\n"
    "    }",
    "    if (p >= 100) {\n"
    "      clearInterval(GEN_TIMER);\n"
    "      if (STATE.rec && STATE.rec.tables && BRIDGE_OK) {\n"
    "        renderReport();\n"
    "      } else {\n"
    "        setTimeout(function () { go('s-result'); }, 450);\n"
    "      }\n"
    "    }"))

# 6) 结果屏：有真文件就用真结果
OLD_FILL = """function fillResult() {
  var r = compute();
  $('k-y').textContent = (r.Y / 1e11).toFixed(3) + '×10¹¹';
  $('k-u').textContent = r.rel.toFixed(2) + '%';
  $('k-e').textContent = (r.Y >= 2e11 ? '+' : '−') + Math.abs((r.Y - 2e11) / 2e11 * 100).toFixed(2) + '%';
  $('res-sub').textContent = STATE.exp + ' · ' + new Date().toISOString().slice(0, 10) +
    ' · ' + fmtList() + (STATE.regenerated ? ' · 第 ' + (STATE.regenerated + 1) + ' 版' : '') +
    (STATE.demo ? ' · 示例数据（不能直接提交）' : '');
}"""
NEW_FILL = """function fillResult() {
  var ks = document.querySelectorAll('#s-result .kpi .k');
  var dl = $('btn-dl');
  if (STATE.out && STATE.out.result) {
    var o = STATE.out.result;
    $('k-y').textContent = (o.h * 1e34).toFixed(3);
    $('k-u').textContent = (o.rel_err_pct >= 0 ? '+' : '−') + Math.abs(o.rel_err_pct).toFixed(2) + '%';
    $('k-e').textContent = (o.u_h * 1e34).toFixed(3);
    if (ks.length >= 3) {
      ks[0].textContent = '普朗克常量 h / 10⁻³⁴ J·s';
      ks[1].textContent = '与公认值 6.626 的相对误差';
      ks[2].textContent = '不确定度 u(h) / 10⁻³⁴ J·s';
    }
    dl.textContent = '下载 ' + STATE.out.name + '（' + Math.round(STATE.out.bytes / 1024) + ' KB）';
    dl.onclick = function () { window.location.href = BRIDGE + STATE.out.url; };
  } else {
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
  }
  $('res-sub').textContent = STATE.exp + ' · ' + new Date().toISOString().slice(0, 10) +
    ' · ' + fmtList() + (STATE.regenerated ? ' · 第 ' + (STATE.regenerated + 1) + ' 版' : '') +
    (STATE.demo ? ' · 示例数据（不能直接提交）' : '');
}"""
PATCHES.append((OLD_FILL, NEW_FILL))

# 7) identify：支持桩数据模式
PATCHES.append((
    "    setRec('正在识别照片（约 5–15 秒）…', 'wait');\n"
    "    fetch(BRIDGE + '/recognize', {\n"
    "      method: 'POST', headers: { 'Content-Type': 'application/json' },\n"
    "      body: JSON.stringify({\n"
    "        exp_id: eid, image_b64: b64, mime: mime,\n"
    "        api_key: (STATE.api && STATE.api.key) || '',\n"
    "        base_url: (STATE.api && STATE.api.url) || '',\n"
    "        model: (STATE.api && STATE.api.model) || ''\n"
    "      })\n"
    "    }).then(",
    "    setRec(STATE.mockRec ? '正在用桩数据识别（不联网、不花钱）…' : '正在识别照片（约 5–15 秒）…', 'wait');\n"
    "    var payload = {\n"
    "      exp_id: eid, image_b64: b64, mime: mime,\n"
    "      api_key: (STATE.api && STATE.api.key) || '',\n"
    "      base_url: (STATE.api && STATE.api.url) || '',\n"
    "      model: (STATE.api && STATE.api.model) || ''\n"
    "    };\n"
    "    if (STATE.mockRec) payload.mode = 'mock';\n"
    "    fetch(BRIDGE + '/recognize', {\n"
    "      method: 'POST', headers: { 'Content-Type': 'application/json' },\n"
    "      body: JSON.stringify(payload)\n"
    "    }).then("))

# 8) API 屏加按钮
PATCHES.append((
    '<button class="btn ghost" onclick="useDemo()">没有密钥？用示例数据体验</button>',
    '<button class="btn ghost" onclick="useDemo()">没有密钥？用示例数据体验</button>\n'
    '            <button class="btn ghost" onclick="useMockRec()">没有密钥？用桩数据试识别</button>'))

# 9) 桩数据模式的函数
PATCHES.append((
    '/* ---------- S3 ---------- */\nfunction officialTap() {',
    '''/* ---------- S3 ---------- */
function useMockRec() {
  STATE.mockRec = true;
  STATE.demo = false;
  var b = $('demo-banner');
  if (b) b.style.display = 'block';
  if (b) b.textContent = '桩数据模式：识别不联网、不花钱，报告会标注「示例数据（不能直接提交）」。';
  var c = $('cost');
  if (c) c.textContent = '桩数据模式：不调用模型，也不消耗额度';
  syncGen();
  go('s-upload');
  toast('已切到桩数据模式：其他流程都一样，只是识别结果不是真的');
}

function officialTap() {'''))

for i, (old, new) in enumerate(PATCHES, 1):
    n = s.count(old)
    if n != 1:
        print('[SKIP %d] 命中 %d 次：%r' % (i, n, old[:60]))
        continue
    s = s.replace(old, new, 1)
    print('[OK   %d] +%d chars  %r' % (i, len(new) - len(old), new[:48]))

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('total %d -> %d chars' % (orig, len(s)))
