# -*- coding: utf-8 -*-
"""核对屏改版：右栏那一堆「助手气泡」→ 表格下方的一道道选择题（横向选项、一次一题）。"""
import io

P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(P, encoding='utf-8').read()
orig = s

# ---------- 1. 布局：去掉两栏，改成「表格 + 选择题目」竖排 ----------
old_start = s.find('    <div class="grid2" style="grid-template-columns:1.35fr 1fr">')
old_end = s.find('  </section>', old_start)
assert old_start > 0 and old_end > old_start
old_block = s[old_start:old_end]

new_block = '''    <div id="rec-note" class="hint" style="display:none;margin-bottom:8px"></div>
    <div id="rec-wrap" style="display:none"></div>
    <div class="tablewrap" id="t-review-wrap">
      <table class="grid" id="t-review">
        <thead>
          <tr><th>次数</th><th>荷载/kg</th><th>增重读数</th><th>减重读数</th><th>平均</th><th>N</th></tr>
        </thead>
        <tbody id="t-review-body"></tbody>
      </table>
    </div>
    <div class="hint">单位 10⁻² m。表里显示几位，计算就用几位。</div>
    <div id="conflict"></div>

    <!-- 选择题：一次一道，和表格同宽，选项横向排 -->
    <div id="quiz" class="quiz" style="display:none">
      <div class="qtop">
        <span class="qno">第 <b id="q-idx">1</b> / <b id="q-total">1</b> 题</span>
        <span class="qloc" id="q-loc"></span>
      </div>
      <div class="qwhy" id="q-why"></div>
      <div class="qopts" id="q-opts"></div>
      <div class="qfoot">
        <span class="qtip" id="q-tip">选一个，或者先去表里直接改那个格子</span>
        <button class="btn sm" type="button" onclick="qSkip()">先跳过这题</button>
      </div>
    </div>

    <div class="qact">
      <button class="btn pri" id="btn-ok" onclick="go('s-gen')" disabled>数字都对，生成报告</button>
      <div class="hint" id="ok-hint">先看下面：有几道题等你选。</div>
    </div>
'''
s = s[:old_start] + new_block + s[old_end:]

# ---------- 2. CSS ----------
css_anchor = '.rtitle{font-weight:700;font-size:14px;margin:2px 0 2px}'
assert css_anchor in s
css_new = '''.quiz{border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:14px 0 10px;background:#fff}
  .qtop{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:6px}
  .qno{font-size:12px;color:#8a939c}
  .qloc{font-weight:700;font-size:14.5px;color:#22303c}
  .qwhy{color:#5b6672;font-size:13px;line-height:1.7;margin-bottom:10px}
  .qopts{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
  .qopt{display:inline-flex;align-items:center;gap:6px;padding:7px 14px;border:1px solid #cfd8e3;
    border-radius:999px;background:#fbfcfd;font-size:14px;cursor:pointer;line-height:1}
  .qopt:hover{border-color:var(--pri);background:#f2f7ff}
  .qopt b{font-weight:700;font-variant-numeric:tabular-nums}
  .qopt.cur{border-style:dashed;color:#3b6ea5}
  .qopt.sel{border-color:var(--pri);background:var(--pri);color:#fff}
  .qfoot{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-top:12px}
  .qtip{font-size:12px;color:#8a939c}
  .qact{margin-top:12px;display:flex;flex-direction:column;gap:6px;align-items:flex-start}
  .grid td.hl{background:#fff7d6;box-shadow:inset 0 0 0 2px #f0c36d}
  .rtitle{font-weight:700;font-size:14px;margin:2px 0 2px}'''
s = s.replace(css_anchor, css_new, 1)

# ---------- 3. recTableHtml：给每格打上 data-t/r/c，好定位高亮与回写 ----------
old = '''function recTableHtml(tb) {
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
}'''
new = '''function recTableHtml(tb, tid) {
  var rows = (tb && tb.cells) || [], h = '', ri, ci, r, c;
  if (!rows.length) return '';
  h = '<div class="tablewrap" style="margin-bottom:10px"><table class="grid" data-t="' + tid + '">';
  for (ri = 0; ri < rows.length; ri++) {
    r = rows[ri];
    h += '<tr>';
    for (ci = 0; ci < r.length; ci++) {
      c = esc(r[ci]);
      h += (ri === 0 ? '<th>' + c + '</th>'
        : '<td class="num" data-t="' + tid + '" data-r="' + ri + '" data-c="' + ci + '">' + c + '</td>');
    }
    h += '</tr>';
  }
  return h + '</table></div>';
}'''
assert old in s
s = s.replace(old, new, 1)

# ---------- 4. buildReviewFromRec：改成出题 ----------
i = s.find('function buildReviewFromRec() {')
j = s.find('/* ---------- S6 生成', i)
assert i > 0 and j > i
old_fn = s[i:j]

new_fn = '''function buildReviewFromRec() {
  var rec = STATE.rec, i;
  $('t-review-wrap').style.display = 'none';
  $('rec-wrap').style.display = 'block';
  renderRecTables();

  var img = (rec.meta && rec.meta.image) || {};
  var note = $('rec-note');
  note.style.display = 'block';
  note.textContent = (img.converted_from === 'heic' ? '照片已自动转码 HEIC → JPEG：' : '已识别：') +
    (img.out_size || []).join('×') + '，' + (img.out_kb || '?') + ' KB（原始 ' +
    (img.in_kb || '?') + ' KB）';

  buildQuiz();
}

function renderRecTables() {
  var rec = STATE.rec, html = '';
  ['t1', 't2', 't3'].forEach(function (k) {
    if (rec.tables[k]) html += recTableHtml(rec.tables[k], k);
  });
  $('rec-wrap').innerHTML = html || ('<div class="empty">这张照片里没认出表格。<br>建议只拍表格那一片、正对着拍、别反光；也可能是拍错了实验。' +
    '<div style="margin-top:10px"><button class="btn" onclick="go(\\'s-upload\\')">换一张照片</button></div></div>');
}

/* ---------- 出题：每个疑点一道，选项横向排，一次只显示一道 ---------- */
var QUIZ = { list: [], i: 0, done: {} };

function buildQuiz() {
  var notes = (STATE.rec && STATE.rec.notes) || [];
  QUIZ = { list: notes.slice(0), i: 0, done: {} };
  var box = $('quiz');
  if (!QUIZ.list.length) {
    box.style.display = 'none';
    $('btn-ok').disabled = false;
    $('ok-hint').textContent = '识别没有发现疑点，可以直接生成。';
    return;
  }
  box.style.display = 'block';
  QUIZ.i = 0;
  renderQ();
}

function qTarget(q) {
  return (q.table && q.row >= 0 && q.col >= 0) ? { t: q.table, r: q.row, c: q.col } : null;
}

function qValueAt(q) {
  var tg = qTarget(q);
  if (!tg) return '';
  var cells = (STATE.rec.tables[tg.t] || {}).cells || [];
  return (cells[tg.r] && cells[tg.r][tg.c] != null) ? String(cells[tg.r][tg.c]) : '';
}

function renderQ() {
  var q = QUIZ.list[QUIZ.i], n = QUIZ.list.length;
  if (!q) return;
  $('q-idx').textContent = QUIZ.i + 1;
  $('q-total').textContent = n;
  $('q-loc').textContent = q.where || '（这一格）';

  var cur = qValueAt(q) || q.current || '';
  var why = q.why ? ('模型说：' + q.why + '。') : '';
  $('q-why').textContent = why + '它现在填的是 ' + (cur === '' ? '（空）' : cur) +
    (q.candidates && q.candidates.length > 1 ? '，下面这些是它拿不准的可能值。' : '。');

  var opts = (q.candidates || []).slice(0);
  if (cur && opts.indexOf(cur) < 0) opts.unshift(cur);
  if (!opts.length) opts.push(cur || '');
  var h = '';
  for (var k = 0; k < opts.length; k++) {
    var v = opts[k];
    h += '<button type="button" class="qopt' + (v === cur ? ' cur' : '') +
      '" onclick="qPick(\\'' + esc(String(v)).replace(/'/g, "\\\\'") + '\\')"><b>' + esc(v) + '</b>' +
      (v === cur ? '<span style="font-size:11px;opacity:.7">模型填的</span>' : '') + '</button>';
  }
  h += '<button type="button" class="qopt" onclick="qManual()">都不是，我自己填…</button>';
  $('q-opts').innerHTML = h;
  $('q-tip').textContent = '选一个就会写进表里第 ' + (QUIZ.i + 1) + '/' + n + ' 题；也可以直接改表里的格子。';
  hlCell(q);
}

function hlCell(q) {
  var all = document.querySelectorAll('#rec-wrap td.hl');
  for (var k = 0; k < all.length; k++) all[k].classList.remove('hl');
  var tg = qTarget(q);
  if (!tg) return;
  var sel = '#rec-wrap td[data-t="' + tg.t + '"][data-r="' + tg.r + '"][data-c="' + tg.c + '"]';
  var td = document.querySelector(sel);
  if (td) td.classList.add('hl');
}

function qPick(v) {
  var q = QUIZ.list[QUIZ.i];
  var tg = qTarget(q);
  if (tg) {
    var tb = STATE.rec.tables[tg.t] || {};
    if (!tb.cells) tb.cells = [];
    if (!tb.cells[tg.r]) tb.cells[tg.r] = [];
    tb.cells[tg.r][tg.c] = v;
    renderRecTables();
    saveDraft();
  }
  QUIZ.done[q.id] = v;
  qNext();
}

function qManual() {
  var q = QUIZ.list[QUIZ.i];
  var tg = qTarget(q);
  if (!tg) { toast('这一题模型没给准位置，直接去表里找到那格改吧'); return; }
  var old = qValueAt(q);
  var v = window.prompt('这一格应该是多少？（' + (q.where || '') + '）', old);
  if (v === null) return;
  v = String(v).trim();
  if (!v) return;
  qPick(v);
}

function qSkip() {
  var q = QUIZ.list[QUIZ.i];
  QUIZ.done[q.id] = null;
  qNext();
}

function qNext() {
  var n = QUIZ.list.length;
  for (var k = 1; k <= n; k++) {
    var idx = (QUIZ.i + k) % n;
    if (!(QUIZ.list[idx].id in QUIZ.done)) { QUIZ.i = idx; renderQ(); updateQuizState(); return; }
  }
  updateQuizState();
}

function updateQuizState() {
  var n = QUIZ.list.length, left = 0, k;
  for (k = 0; k < n; k++) if (!(QUIZ.list[k].id in QUIZ.done)) left++;
  var box = $('quiz');
  if (left === 0) {
    box.style.display = 'none';
    $('btn-ok').disabled = false;
    $('ok-hint').textContent = '题目都过完了（共 ' + n + ' 题），可以生成报告。';
  } else {
    box.style.display = 'block';
    $('btn-ok').disabled = true;
    $('ok-hint').textContent = '还有 ' + left + ' 题等你选。';
  }
}

'''
s = s[:i] + new_fn + s[j:]

# ---------- 5. 数据页失败时把旧的两栏状态复位 ----------
old = """  var ic = $('issue-n');"""
if old in s:
    s = s.replace(old, """  var ic = $('issue-n');""", 1)

assert s != orig
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[OK] review screen rebuilt, %d -> %d chars' % (len(orig), len(s)))
