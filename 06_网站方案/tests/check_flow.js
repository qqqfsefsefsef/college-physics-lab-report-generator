// 端到端验证用户报的两个 bug：①点「生成报告」能跳转 ②没填 key 也不卡死、重复点「测试连接」不重复请求
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'prototype_v2.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];

/* ---------- 极简 DOM 桩 ---------- */
const els = {};
function fakeEl(id) {
  const on = new Set();
  const t = {
    id, value: '', textContent: '', innerHTML: '', disabled: false, type: 'password',
    style: {}, dataset: {},
    classList: {
      add(n) { on.add(n); }, remove(n) { on.delete(n); },
      toggle(n) { if (on.has(n)) on.delete(n); else on.add(n); }, contains(n) { return on.has(n); },
    },
    focus() { t.__focus = true; },
    addEventListener() {}, appendChild() { return fakeEl('child'); }, remove() {},
    setAttribute() {}, scrollIntoView() {}, querySelectorAll() { return []; }, querySelector() { return null; },
  };
  t.__on = on;
  return t;
}
const document = {
  getElementById(id) { return els[id] || (els[id] = fakeEl(id)); },
  querySelector() { return null; },
  querySelectorAll(sel) { return sel === '.screen' ? Object.values(els).filter((e) => e.__on) : []; },
  createElement() { return fakeEl('tmp'); },
  addEventListener() {}, body: fakeEl('body'), documentElement: fakeEl('html'),
};
const localStorage = { getItem() { return null; }, setItem() {}, removeItem() {} };
const timers = [];
function setTimeout(fn) { timers.push(fn); return timers.length; }
function flush() { while (timers.length) timers.shift()(); }
const window = { localStorage, document, setTimeout, addEventListener() {}, scrollTo() {}, matchMedia() { return { matches: false }; } };
global.fetch = function () { return Promise.reject(new Error('no bridge in test')); };
global.FileReader = function () {};
document.getElementById('api-url').value = 'https://api.deepseek.com/v1';
document.getElementById('api-model').value = 'deepseek-v4-flash-vision-exp';

const ctx = new Function('document', 'window', 'localStorage', 'setTimeout', 'Date', 'Math', 'JSON',
  'navigator', 'location', 'alert', 'console', script +
  '\n;return {STATE:STATE, go:go, startGen:startGen, nextFromApi:nextFromApi, testConn:testConn,' +
  ' useDemo:useDemo, syncGen:syncGen, compute:compute};');
const api = ctx(document, window, localStorage, setTimeout, Date, Math, JSON,
  { userAgent: 'node' }, { href: '' }, function () {}, console);

function screenOn() {
  const hit = Object.keys(els).filter((k) => els[k].__on && els[k].__on.has('on'));
  return hit.length ? hit[hit.length - 1] : '(none)';
}
let fail = 0;
function ok(name, cond, extra) {
  const line = (cond ? '[OK] ' : '[FAIL] ') + name + (extra ? '  ' + extra : '');
  if (cond) console.log(line); else { console.error(line); fail++; }
}

/* ---------- 1. 示例模式 ---------- */
api.useDemo(); flush();
ok('示例模式下「生成报告」可点', document.getElementById('btn-gen').disabled === false);
const rc = api.compute();
ok('示例数据算得出 Y', Math.abs(rc.Y / 2.0166e11 - 1) < 2e-4,
  'Y=' + (rc.Y / 1e11).toFixed(4) + 'e11 Pa, u/Y=' + rc.rel.toFixed(3) + '%');

/* ---------- 2. bug1：点生成能跳转 ---------- */
api.startGen();
ok('点「生成报告」切到核对屏', screenOn() === 's-review', 'screen=' + screenOn());

/* ---------- 3. bug2-a：没填 key 点「下一步」不卡死 ---------- */
api.go('s-api');
document.getElementById('api-url').value = '';
document.getElementById('api-key').value = '';
api.nextFromApi();
ok('未填项时不跳转', screenOn() === 's-api', 'screen=' + screenOn());
ok('给出缺项提示', /三项都填了才能继续/.test(document.getElementById('api-msg').innerHTML));
ok('焦点落到第一个空输入', document.getElementById('api-url').__focus === true);

/* ---------- 4. bug2-b：连点与重复点都不再请求 ---------- */
timers.length = 0;
global.fetch = function () { return Promise.reject(new Error('no bridge in test')); };
global.FileReader = function () {};
document.getElementById('api-url').value = 'https://api.deepseek.com/v1';
document.getElementById('api-key').value = 'sk-0123456789abcdef';
api.testConn();
ok('第一次进入测试中', document.getElementById('btn-test').disabled === true);
api.testConn();
ok('连点被忽略', timers.length === 1, 'pending=' + timers.length);
flush();
ok('第一次测试通过', /^通过/.test(document.getElementById('api-status').textContent), document.getElementById('api-status').textContent);
timers.length = 0;
api.testConn();
ok('参数未变不再发请求', timers.length === 0, 'pending=' + timers.length);
ok('提示已测过', /已通过 · 未改动/.test(document.getElementById('api-status').textContent));

/* ---------- 5. 已测过再点「下一步」直接放行 ---------- */
api.nextFromApi();
ok('已测过 → 直接进上传屏', screenOn() === 's-upload', 'screen=' + screenOn());

/* ---------- 6. 改了 key 会自动补测一次 ---------- */
api.go('s-api');
document.getElementById('api-key').value = 'sk-0123456789abcdef-XYZ';
timers.length = 0;
api.nextFromApi();
ok('参数改动后自动补测', timers.length === 1, 'pending=' + timers.length);
flush();
ok('补测通过后跳上传屏', screenOn() === 's-upload', 'screen=' + screenOn());

console.log(fail ? ('\n[SUM] ' + fail + ' 项失败') : '\n[SUM] 全部通过');
process.exit(fail ? 1 : 0);
