
/* ---------- 状态 ---------- */
var FLAGS = { official: false };          /* 官方通道开关：上线前保持 false */
var STATE = {
  api: { url: '', model: '', key: '', tested: false },
  files: { data: false, hw: false, shot: false },
  fmt: { pdf: true, docx: true, json: false, png: false },
  exp: '用静态拉伸法测金属丝的杨氏弹性模量',
  reviewed: {},      /* 已确认的问题 id */
  regenerated: 0
};

var $ = function (id) { return document.getElementById(id); };

/* ---------- 屏幕切换 ---------- */
function go(id) {
  var all = document.querySelectorAll('.screen');
  for (var i = 0; i < all.length; i++) all[i].classList.remove('on');
  var el = $(id);
  if (el) el.classList.add('on');
  window.scrollTo({ top: 0, behavior: 'instant' in window ? 'instant' : 'auto' });
  if (id === 's-review') buildReview();
  if (id === 's-gen') runGen();
  if (id === 's-result') fillResult();
}

/* ---------- S0 ---------- */
function openNotice() { $('notice').classList.remove('hide'); }
function acceptNotice() {
  $('notice').classList.add('hide');
  try { localStorage.setItem('notice.ok', '1'); } catch (e) {}
}

/* ---------- S2 ---------- */
function togglePwd() {
  var k = $('api-key');
  k.type = (k.type === 'password') ? 'text' : 'password';
}
function testConn() {
  var u = $('api-url').value.trim(), m = $('api-model').value.trim(), k = $('api-key').value.trim();
  var box = $('api-msg'), st = $('api-status');
  if (!u || !m || !k) {
    box.innerHTML = '<div class="badbox">三项都要填。</div>';
    return;
  }
  st.textContent = '测试中…';
  $('api-next').disabled = true;
  setTimeout(function () {
    if (k.length < 12) {
      st.textContent = '失败';
      box.innerHTML = '<div class="badbox"><b>密钥无效</b>：格式看起来不对（太短）。请回到开放平台复制完整的 key。</div>';
      return;
    }
    if (!/^https?:\/\//.test(u)) {
      st.textContent = '失败';
      box.innerHTML = '<div class="badbox"><b>地址不通</b>：base_url 需要以 http(s):// 开头，并且指向兼容 OpenAI 格式的接口。</div>';
      return;
    }
    if (!/vision|vl|image|v4/i.test(m)) {
      st.textContent = '失败';
      box.innerHTML = '<div class="badbox"><b>模型不支持图片</b>：这个模型读不了照片，本工具需要能看图的模型。</div>';
      return;
    }
    st.textContent = '通过 · 12ms · 16 tokens';
    box.innerHTML = '<div class="okbox">连接成功：模型可用、密钥有效、支持图片输入。</div>';
    STATE.api = { url: u, model: m, key: k, tested: true };
    $('api-next').disabled = false;
  }, 900);
}

/* ---------- S3 ---------- */
function officialTap() {
  if (FLAGS.official) { go('s-code'); return; }
  toast('官方通道未开放，想内测可以联系作者拿兑换码');
}

/* ---------- S4 ---------- */
function toggleExp() {
  var s = $('exp-sel');
  s.style.display = (s.style.display === 'none') ? 'block' : 'none';
  s.onchange = function () { STATE.exp = s.value; $('exp-detect').textContent = s.value; };
}
function pick(input, upId, fnId) {
  var f = input.files && input.files[0];
  if (!f) return;
  $(fnId).textContent = f.name;
  $(upId).classList.add('done');
  if (upId === 'up-data') STATE.files.data = true;
  if (upId === 'up-hw') STATE.files.hw = true;
  if (upId === 'up-shot') STATE.files.shot = true;
  syncGen();
}
function toggleFmt(btn) {
  var f = btn.getAttribute('data-f');
  STATE.fmt[f] = !STATE.fmt[f];
  if (STATE.fmt[f]) btn.classList.add('on'); else btn.classList.remove('on');
  if (!STATE.fmt.pdf && !STATE.fmt.docx && !STATE.fmt.json && !STATE.fmt.png) {
    STATE.fmt.pdf = true; document.querySelector('[data-f=pdf]').classList.add('on');
    toast('至少留一个格式，已帮你勾回 PDF');
  }
}
function syncGen() {
  var need = [];
  if (!STATE.files.data) need.push('原始数据页');
  if (!STATE.files.hw) need.push('以前的作业');
  var ok = need.length === 0;
  $('btn-gen').disabled = !ok;
  $('gen-hint').textContent = ok ? '齐了，可以生成' : ('还差：' + need.join('、'));
}
function fmtList() {
  var names = { pdf: 'PDF', docx: 'Word', json: 'JSON', png: 'PNG' }, out = [];
  for (var k in STATE.fmt) if (STATE.fmt[k]) out.push(names[k]);
  return out.join(' + ');
}

/* ---------- 计算（真算） ---------- */
var DATA = {
  up:   [10.00, 12.79, 15.57, 18.36, 21.13, 23.92, 26.70, 29.48],
  down: [10.03, 12.82, 15.60, 18.39, 21.17, 23.95, 26.73, 29.51],
  dia:  [0.298, 0.301, 0.299, 0.302, 0.300, 0.301]
};
var CONST = { K: 0.0750, D: 1.5000, L: 1.0000, g: 9.794, zero: 0.002, m4: 4.0 };

function avg(a) { var s = 0; for (var i = 0; i < a.length; i++) s += a[i]; return s / a.length; }

function compute() {
  var mean = [], i;
  for (i = 0; i < 8; i++) mean.push((DATA.up[i] + DATA.down[i]) / 2);
  var N = [];
  for (i = 0; i < 4; i++) N.push(mean[i + 4] - mean[i]);
  var Nbar = avg(N), S = 0;
  for (i = 0; i < 4; i++) S += Math.pow(N[i] - Nbar, 2);
  S = Math.sqrt(S / 3);
  var Sbar = S / 2;
  var dbar = avg(DATA.dia), d = dbar - CONST.zero;
  var F = CONST.m4 * CONST.g;
  var Y = 8 * F * CONST.L * CONST.D / (Math.PI * Math.pow(d / 1000, 2) * CONST.K * (Nbar / 100));
  var ur = [
    2 * 0.004 / d * 100,
    0.0005 / CONST.K * 100,
    0.002 / CONST.D * 100,
    0.0005 / CONST.L * 100,
    0.5,
    Sbar / Nbar * 100
  ];
  var q = 0;
  for (i = 0; i < ur.length; i++) q += ur[i] * ur[i];
  var rel = Math.sqrt(q);
  return { mean: mean, N: N, Nbar: Nbar, S: S, Sbar: Sbar, dbar: dbar, d: d, F: F, Y: Y, rel: rel, uY: Y * rel / 100 };
}

/* ---------- S5 核对 ---------- */
var ISSUES = [
  {
    id: 'x1', level: 'warn', text: '表 1 第 0 行：增重 10.00、减重 10.03，两次差 0.03，属正常迟滞；已按平均值参与逐差。', btn: '知道了'
  },
  {
    id: 'x2', level: 'warn', text: '千分尺零点读数 0.002 mm 已记下，直径会先减零点再平方，别忘这一步。', btn: '知道了'
  }
];

function buildReview() {
  var r = compute(), body = $('t-review-body');
  var html = '', i;
  for (i = 0; i < 8; i++) {
    html += '<tr>' +
      '<td>' + i + '</td>' +
      '<td class="num">' + (2 + i).toFixed(3) + '</td>' +
      '<td><input data-i="' + i + '" data-k="up" value="' + DATA.up[i].toFixed(2) + '"></td>' +
      '<td><input data-i="' + i + '" data-k="down" value="' + DATA.down[i].toFixed(2) + '"></td>' +
      '<td class="num">' + r.mean[i].toFixed(3) + '</td>' +
      '<td class="num">' + (i < 4 ? r.N[i].toFixed(3) : '') + '</td>' +
      '</tr>';
  }
  body.innerHTML = html;
  var inputs = body.querySelectorAll('input');
  for (i = 0; i < inputs.length; i++) {
    inputs[i].onchange = function () {
      var idx = +this.getAttribute('data-i'), key = this.getAttribute('data-k');
      var v = parseFloat(this.value);
      if (isNaN(v)) { toast('请输入数字'); return; }
      DATA[key][idx] = v;
      this.parentNode.classList.add('changed');
      var rr = compute();
      var rows = body.querySelectorAll('tr');
      for (var j = 0; j < 8; j++) {
        rows[j].children[4].textContent = rr.mean[j].toFixed(3);
        rows[j].children[5].textContent = (j < 4 ? rr.N[j].toFixed(3) : '');
      }
      var d = rr.Nbar - avg(rr.N);
      $('conflict').innerHTML = '';
      document.querySelectorAll('#chat .msg.bot').forEach(function (m) {});
    };
  }
  var chat = $('chat');
  chat.innerHTML = '';
  for (i = 0; i < ISSUES.length; i++) addMsg('bot', ISSUES[i].text, ISSUES[i].id);
  STATE.reviewed = {};
  $('btn-ok').disabled = true;
  $('ok-hint').textContent = '把上面 ' + ISSUES.length + ' 条各点一次「知道了」才能继续。';
  $('conflict').innerHTML = '';
}

function addMsg(who, text, id) {
  var chat = $('chat'), div = document.createElement('div');
  div.className = 'msg ' + who;
  div.innerHTML = '<div class="who">' + (who === 'bot' ? '助手' : '我') + '</div>' + text;
  if (id) {
    var b = document.createElement('button');
    b.className = 'btn sm';
    b.style.marginTop = '8px';
    b.textContent = '知道了';
    b.onclick = function () {
      STATE.reviewed[id] = true;
      div.style.opacity = '.55';
      b.disabled = true;
      b.textContent = '已确认';
      var left = ISSUES.length - Object.keys(STATE.reviewed).length;
      if (left <= 0) {
        $('btn-ok').disabled = false;
        $('ok-hint').textContent = '都确认过了，可以开始生成。';
      } else {
        $('ok-hint').textContent = '还剩 ' + left + ' 条要确认。';
      }
    };
    div.appendChild(document.createElement('div')).appendChild(b);
  }
  chat.appendChild(div);
}

/* ---------- S6 生成 ---------- */
var GEN_TIMER = null;
function runGen() {
  var bar = $('gen-bar'), step = $('gen-step'), p = 0;
  var stages = ['识别原始数据页…', '重建表格并逐格核对…', '按公式计算与不确定度合成…', '套用学校模板排版…', '渲染 PDF / Word…'];
  $('btn-ok').disabled = true;
  if (GEN_TIMER) clearInterval(GEN_TIMER);
  GEN_TIMER = setInterval(function () {
    p += 4;
    if (p > 100) p = 100;
    bar.style.width = p + '%';
    var s = Math.min(stages.length - 1, Math.floor(p / 20));
    step.textContent = stages[s] + '  ' + p + '%';
    if (p >= 100) {
      clearInterval(GEN_TIMER);
      setTimeout(function () { go('s-result'); }, 450);
    }
  }, 90);
}

/* ---------- S7 结果 ---------- */
function fillResult() {
  var r = compute();
  $('k-y').textContent = (r.Y / 1e11).toFixed(3) + '×10¹¹';
  $('k-u').textContent = r.rel.toFixed(2) + '%';
  $('k-e').textContent = (r.Y >= 2e11 ? '+' : '−') + Math.abs((r.Y - 2e11) / 2e11 * 100).toFixed(2) + '%';
  $('res-sub').textContent = STATE.exp + ' · ' + new Date().toISOString().slice(0, 10) +
    ' · ' + fmtList() + (STATE.regenerated ? ' · 第 ' + (STATE.regenerated + 1) + ' 版' : '');
}

/* ---------- S8 重新生成 ---------- */
function regen() {
  STATE.regenerated++;
  toast('已记录原因，进入重新生成');
  go('s-gen');
}

/* ---------- S9 清理 ---------- */
function cleanCk() {
  var ok = $('c1').checked && $('c2').checked && $('c3').checked;
  $('btn-clean').disabled = !ok;
}
function doneClean() {
  STATE.api = { url: '', model: '', key: '', tested: false };
  $('api-key').value = '';
  $('api-url').value = 'https://api.deepseek.com/v1';
  $('api-model').value = 'deepseek-v4-flash-vision-exp';
  $('api-msg').innerHTML = '';
  $('api-status').textContent = '未测试';
  $('api-next').disabled = true;
  toast('已清除本地密钥，回到首页');
  setTimeout(function () { go('s-home'); }, 700);
}

/* ---------- toast ---------- */
var toastTimer = null;
function toast(msg) {
  var t = $('toast');
  t.textContent = msg;
  t.classList.add('on');
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(function () { t.classList.remove('on'); }, 2600);
}

/* ---------- 启动 ---------- */
(function boot() {
  var seen = null;
  try { seen = localStorage.getItem('notice.ok'); } catch (e) {}
  if (seen) $('notice').classList.add('hide');
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !$('notice').classList.contains('hide')) acceptNotice();
  });
  syncGen();
  if (FLAGS.official) {
    $('official-tag').textContent = '可用';
    $('official-tag').classList.remove('gray');
    $('card-official').classList.remove('off');
  }
})();
