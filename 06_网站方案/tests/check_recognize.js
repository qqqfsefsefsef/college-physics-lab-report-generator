// 真实链路验证：上传照片 → 本地识别桥（07_流水线/bridge.py --mock）→ 回填表格 → 解锁生成
// 前提：bridge.py 以 --mock 跑在 127.0.0.1:8732
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'prototype_v2.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];

const els = {};
function fakeEl(id) {
  const on = new Set();
  const t = {
    id, value: '', textContent: '', innerHTML: '', disabled: false, type: 'password',
    style: {}, dataset: {},
    classList: { add(n) { on.add(n); }, remove(n) { on.delete(n); }, toggle(n) { if (on.has(n)) on.delete(n); else on.add(n); }, contains(n) { return on.has(n); } },
    focus() {}, addEventListener() {}, appendChild() { return fakeEl('child'); }, remove() {},
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
/* FileReader 桩：立刻吐出 base64 */
global.FileReader = function () {
  const self = this;
  this.readAsDataURL = function (file) {
    setTimeout(function () { self.result = 'data:image/jpeg;base64,' + (file.__b64 || 'AAAA'); self.onload(); }, 0);
  };
};
const window = { localStorage, document, setTimeout, addEventListener() {}, scrollTo() {}, matchMedia() { return { matches: false }; } };

const ctx = new Function('document', 'window', 'localStorage', 'setTimeout', 'Date', 'Math', 'JSON',
  'navigator', 'location', 'alert', 'console', script +
  '\n;return {STATE:STATE, go:go, pick:pick, identify:identify, probeBridge:probeBridge, syncGen:syncGen,' +
  ' setRec:setRec, screenOn:function(){return null;}};');
const api = ctx(document, window, localStorage, setTimeout, Date, Math, JSON,
  { userAgent: 'node' }, { href: '' }, function () {}, console);

let fail = 0;
function ok(name, cond, extra) {
  const line = (cond ? '[OK] ' : '[FAIL] ') + name + (extra ? '  ' + extra : '');
  if (cond) console.log(line); else { console.error(line); fail++; }
}
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

(async function () {
  api.STATE.exp = '钨的逸出功测定';       /* 桩数据只有这个实验 */
  api.STATE.mockRec = true;                /* 让桥走桩数据，不需要密钥 */
  api.go('s-upload');
  await wait(700);
  const st0 = document.getElementById('rec-status').textContent;
  ok('进上传屏会自动探活识别桥', /识别桥已连接/.test(st0), st0);

  const file = { name: 'data.jpg', type: 'image/jpeg',
    __b64: fs.readFileSync(path.join(__dirname, 'fixture.b64'), 'utf8').trim() };
  api.pick({ files: [file] }, 'up-data', 'fn-data');
  await wait(1500);

  const st1 = document.getElementById('rec-status').textContent;
  ok('识别完成提示', /识别完成/.test(st1), st1);
  ok('回填了 STATE.rec', !!(api.STATE.rec && api.STATE.rec.tables && api.STATE.rec.tables.t1),
    api.STATE.rec ? JSON.stringify(Object.keys(api.STATE.rec.tables)) : '(空)');
  const cells = api.STATE.rec && api.STATE.rec.tables.t1.cells;
  ok('表 1 是 8×8', !!cells && cells.length === 8 && cells[0].length === 8,
    cells ? cells.length + '×' + cells[0].length : '(无)');
  ok('首格读数正确', cells && cells[0][0] === 23, cells ? String(cells[0][0]) : '');
  ok('预览渲染出表格', /<table class="mini">/.test(document.getElementById('rec-preview').innerHTML));
  ok('歧义提示被带回', (api.STATE.rec.notes || []).length === 1,
    (api.STATE.rec.notes || [])[0] || '');
  ok('数据页被标记为已上传', api.STATE.files.data === true);

  console.log(fail ? ('\n[SUM] ' + fail + ' 项失败') : '\n[SUM] 全部通过');
  process.exit(fail ? 1 : 0);
})();
