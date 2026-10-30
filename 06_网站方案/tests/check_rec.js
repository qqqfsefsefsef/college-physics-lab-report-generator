// 验证「识别结果 → 核对屏 → 结果屏」这段：buildReviewFromRec() 与 fillResult()
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'prototype_v2.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];

const els = {};
const kpiLabels = [];
const kpiValues = [];
function fakeEl(id) {
  const on = new Set();
  const t = {
    id, value: '', textContent: '', innerHTML: '', disabled: false, type: 'password',
    style: {}, dataset: {}, onclick: null,
    classList: {
      add(n) { on.add(n); }, remove(n) { on.delete(n); },
      toggle(n) { if (on.has(n)) on.delete(n); else on.add(n); }, contains(n) { return on.has(n); },
    },
    focus() { t.__focus = true; }, addEventListener() {}, appendChild() { return fakeEl('child'); },
    remove() {}, setAttribute() {}, scrollIntoView() {},
    querySelectorAll() { return []; }, querySelector() { return null; },
  };
  t.__on = on;
  return t;
}
const document = {
  getElementById(id) { return els[id] || (els[id] = fakeEl(id)); },
  querySelector() { return null; },
  querySelectorAll(sel) {
    if (sel === '#s-result .kpi .k') return kpiLabels;
    if (sel === '#s-result .kpi .v') return kpiValues;
    return [];
  },
  createElement() { return fakeEl('tmp'); },
  addEventListener() {}, body: fakeEl('body'), documentElement: fakeEl('html'),
};
for (let i = 0; i < 3; i++) kpiLabels.push(fakeEl('k' + i));
for (let i = 0; i < 3; i++) kpiValues.push(fakeEl('v' + i));
const localStorage = { getItem() { return null; }, setItem() {}, removeItem() {} };
const timers = [];
function setTimeout(fn) { timers.push(fn); return timers.length; }
const window = { localStorage, document, setTimeout, addEventListener() {}, scrollTo() {}, matchMedia() { return { matches: false }; } };
global.fetch = function () { return Promise.reject(new Error('no bridge in test')); };
global.FileReader = function () {};

const ctx = new Function('document', 'window', 'localStorage', 'setTimeout', 'Date', 'Math', 'JSON',
  'navigator', 'location', 'alert', 'console', script +
  '\n;return {STATE:STATE, buildReviewFromRec:buildReviewFromRec, fillResult:fillResult, compute:compute,' +
  ' qPick:qPick, qSkip:qSkip, buildQuiz:buildQuiz, QUIZ:QUIZ};');
const api = ctx(document, window, localStorage, setTimeout, Date, Math, JSON,
  { userAgent: 'node' }, { href: '' }, function () {}, console);

let fail = 0;
function ok(name, cond, extra) {
  const line = (cond ? '[OK] ' : '[FAIL] ') + name + (extra ? '  ' + extra : '');
  if (cond) console.log(line); else { console.error(line); fail++; }
}

const t1 = {
  cells: [['测量数组', '1', '2', '3'],
          ['435.8 nm  U_AK/V', '-4', '-3', '-2'],
          ['I/(10⁻¹¹A)', '0.9', '1.3', '1.7']],
};
api.STATE.rec = {
  tables: { t1, t2: { cells: [['波长', 'Φ=2', 'Φ=4', 'Φ=8'], ['435.8nm', '46.8', '173', '687.0']] } },
  notes: [{
    id: 'q0', table: 't1', row: 2, col: 1,
    where: '表1 · 546.1nm / Φ=4 mm · U_AK = −4 V 那一格',
    current: '0.5', candidates: ['0.5', '0.4'], why: '有涂改',
  }],
  meta: { mode: 'mock', image: { converted_from: 'heic', in_kb: 1433.6, out_kb: 232.2, out_size: [1200, 1600] } },
};

api.buildReviewFromRec();
ok('核对屏改用识别结果（原表1 隐藏）', document.getElementById('t-review-wrap').style.display === 'none');
ok('渲染了识别到的表格', /<table/.test(document.getElementById('rec-wrap').innerHTML) &&
  /<th>/.test(document.getElementById('rec-wrap').innerHTML) &&
  /435\.8 nm/.test(document.getElementById('rec-wrap').innerHTML));
ok('两张表都渲染', (document.getElementById('rec-wrap').innerHTML.match(/<table/g) || []).length === 2);
ok('转码提示带尺寸与体积', /HEIC → JPEG/.test(document.getElementById('rec-note').textContent) &&
  /1200×1600/.test(document.getElementById('rec-note').textContent) &&
  /232\.2 KB/.test(document.getElementById('rec-note').textContent),
  document.getElementById('rec-note').textContent);
ok('有一条待确认时禁点确认', document.getElementById('btn-ok').disabled === true,
  document.getElementById('ok-hint').textContent);

/* 选择题：一次一道，选项横向排，题目要写清数据在哪 */
ok('题目区显示出来了', document.getElementById('quiz').style.display === 'block');
ok('题号是 1/1', document.getElementById('q-idx').textContent === 1 &&
  document.getElementById('q-total').textContent === 1,
  document.getElementById('q-idx').textContent + '/' + document.getElementById('q-total').textContent);
ok('题目写清了数据位置', /表1/.test(document.getElementById('q-loc').textContent) &&
  /546\.1nm/.test(document.getElementById('q-loc').textContent) &&
  /−4 V/.test(document.getElementById('q-loc').textContent),
  document.getElementById('q-loc').textContent);
ok('有多个选项 + 自己填', (document.getElementById('q-opts').innerHTML.match(/qopt/g) || []).length >= 3,
  (document.getElementById('q-opts').innerHTML.match(/qopt/g) || []).length + ' 个');
ok('选项是横向排布的按钮', /class="qopt/.test(document.getElementById('q-opts').innerHTML));

/* 选一个 → 写回表格 → 题目清空 → 放行 */
api.qPick('0.4');
ok('选完写回识别结果', String(api.STATE.rec.tables.t1.cells[2][1]) === '0.4',
  String(api.STATE.rec.tables.t1.cells[2][1]));
ok('题目清空、放行', document.getElementById('quiz').style.display === 'none' &&
  document.getElementById('btn-ok').disabled === false,
  document.getElementById('ok-hint').textContent);

api.STATE.rec.notes = [];
api.buildReviewFromRec();
ok('没有疑点时直接放行', document.getElementById('btn-ok').disabled === false,
  document.getElementById('ok-hint').textContent);

/* 结果屏：真有 docx 时按实验定义渲染三个 KPI，下载按钮指向桥 */
api.STATE.out = {
  name: '光电效应的研究.docx', bytes: 1493903, url: '/file?path=web-photo-x/out/a.docx',
  result: { h: 6.7504e-34, rel_err_pct: 1.8806, u_h: 9.06e-35 },
  kpi: [
    { label: '普朗克常量 h / 10⁻³⁴ J·s', key: 'h', scale: 1e34, digits: 3 },
    { label: '与公认值 6.626 的相对误差', key: 'rel_err_pct', digits: 2, signed: true, suffix: '%' },
    { label: '不确定度 u(h) / 10⁻³⁴ J·s', key: 'u_h', scale: 1e34, digits: 3 },
  ],
};
api.fillResult();
ok('KPI1 = h', kpiValues[0].textContent === '6.750', kpiValues[0].textContent);
ok('KPI2 = 相对误差', kpiValues[1].textContent === '+1.88%', kpiValues[1].textContent);
ok('KPI3 = u(h)', kpiValues[2].textContent === '0.906', kpiValues[2].textContent);
ok('KPI 标题跟着实验变', kpiLabels[0].textContent.indexOf('普朗克常量') === 0, kpiLabels[0].textContent);

/* 换个实验（杨氏模量）应换成 Y 与相对不确定度，而不是 NaN */
api.STATE.out = {
  name: '杨氏模量.docx', bytes: 1491800, url: '/file?path=web-young-x/out/a.docx',
  result: { Y_Pa: 2.0166e11, u_Y_Pa: 5.73e9, rel_u: 0.0284 },
  kpi: [
    { label: '杨氏模量 Y / 10¹¹ Pa', key: 'Y_Pa', scale: 1e-11, digits: 3 },
    { label: '相对不确定度 u(Y)/Y', key: 'rel_u', scale: 100, digits: 2, suffix: '%' },
    { label: '不确定度 u(Y) / 10¹¹ Pa', key: 'u_Y_Pa', scale: 1e-11, digits: 3 },
  ],
};
api.fillResult();
ok('换实验后 KPI1 = Y', kpiValues[0].textContent === '2.017', kpiValues[0].textContent);
ok('换实验后 KPI2 = 相对不确定度', kpiValues[1].textContent === '2.84%', kpiValues[1].textContent);
ok('换实验后 KPI3 = u(Y)', kpiValues[2].textContent === '0.057', kpiValues[2].textContent);
ok('换实验后没有 NaN', kpiValues.every(function (v) { return !/NaN/.test(v.textContent); }),
  kpiValues.map(function (v) { return v.textContent; }).join(' | '));

api.STATE.out = {
  name: '光电效应的研究.docx', bytes: 1493903, url: '/file?path=web-photo-x/out/a.docx',
  result: { h: 6.7504e-34, rel_err_pct: 1.8806, u_h: 9.06e-35 },
  kpi: [
    { label: '普朗克常量 h / 10⁻³⁴ J·s', key: 'h', scale: 1e34, digits: 3 },
    { label: '与公认值 6.626 的相对误差', key: 'rel_err_pct', digits: 2, signed: true, suffix: '%' },
    { label: '不确定度 u(h) / 10⁻³⁴ J·s', key: 'u_h', scale: 1e34, digits: 3 },
  ],
};
api.fillResult();
ok('下载按钮指向桥的文件', /光电效应的研究\.docx/.test(document.getElementById('btn-dl').textContent) &&
  /1459 KB/.test(document.getElementById('btn-dl').textContent) &&
  typeof document.getElementById('btn-dl').onclick === 'function',
  document.getElementById('btn-dl').textContent);

/* 没有 docx 时：说清楚为什么没生成，不再假装有结果 */
api.STATE.out = null;
api.STATE.outErr = '还没有可用的数据表：这张照片没认出数字';
api.fillResult();
ok('无文件时 KPI 显示占位',
  kpiValues.length === 3 && kpiValues.every(function (v) { return v.textContent === '—'; }),
  kpiValues.map(function (v) { return v.textContent; }).join(' | '));
ok('标题改成「没有生成成功」', document.getElementById('res-h').textContent === '没有生成成功',
  document.getElementById('res-h').textContent);
ok('错误卡显示原因并给出退路',
  /没认出数字/.test(document.getElementById('res-err').innerHTML) &&
  /回去核对数字/.test(document.getElementById('res-err').innerHTML),
  document.getElementById('res-err').innerHTML.slice(0, 60));
ok('下载按钮改成「报告还没生成」', document.getElementById('btn-dl').textContent === '报告还没生成',
  document.getElementById('btn-dl').textContent);

console.log(fail ? '\n[SUM] ' + fail + ' 项失败' : '\n[SUM] 全部通过');
process.exit(fail ? 1 : 0);
