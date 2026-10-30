// 验证 P1 三件事：作业抽风格卡、截图真带进 /render、刷新不丢进度
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'prototype_v2.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];

const els = {};
function fakeEl(id) {
  const on = new Set();
  const t = {
    id, value: '', textContent: '', innerHTML: '', className: '', disabled: false,
    style: {}, dataset: {}, onclick: null, files: null,
    classList: {
      add(n) { on.add(n); }, remove(n) { on.delete(n); },
      toggle(n, f) { if (f === true) on.add(n); else if (f === false) on.delete(n); else if (on.has(n)) on.delete(n); else on.add(n); },
      contains(n) { return on.has(n); },
    },
    focus() {}, addEventListener() {}, appendChild() { return fakeEl('child'); },
    remove() {}, setAttribute() {}, scrollIntoView() {},
    querySelectorAll() { return []; }, querySelector() { return null; },
  };
  t.__on = on;
  return t;
}
const document = {
  getElementById(id) { return els[id] || (els[id] = fakeEl(id)); },
  querySelector() { return null; },
  querySelectorAll() { return []; },
  createElement() { return fakeEl('tmp'); },
  addEventListener() {}, body: fakeEl('body'), documentElement: fakeEl('html'),
};

const store = {};
const localStorage = {
  getItem(k) { return Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null; },
  setItem(k, v) { store[k] = String(v); },
  removeItem(k) { delete store[k]; },
};

const realSetTimeout = global.setTimeout;
const window = {
  localStorage, document,
  setTimeout: realSetTimeout,
  clearTimeout: global.clearTimeout,
  setInterval: function () { return 1; },
  clearInterval: function () {},
  addEventListener() {}, scrollTo() {}, matchMedia() { return { matches: false }; },
};

let lastReq = null;
function fakeResp(obj) {
  return { json: function () { return Promise.resolve(obj); } };
}
global.fetch = function (url, opt) {
  lastReq = { url, body: opt && opt.body ? JSON.parse(opt.body) : null };
  if (url.indexOf('/style') >= 0) {
    return Promise.resolve(fakeResp({
      ok: true, summary: '他/她的报告约 9000 字、114 段，平均句长 44 字（长句铺陈，第三人称书面）',
      stats: { chars: 9000, paras: 114, avg_sentence: 44 },
      prompt_hints: ['硬约束：不得复用他原文里连续 12 个字以上的片段'],
    }));
  }
  if (url.indexOf('/render') >= 0) {
    return Promise.resolve(fakeResp({ ok: true, name: '光电效应的研究.docx', bytes: 100, url: '/file?path=x', kpi: [] }));
  }
  return Promise.resolve(fakeResp({ ok: true }));
};

global.FileReader = function () {
  const self = this;
  this.readAsDataURL = function (f) {
    realSetTimeout(function () { self.result = f.fake; if (self.onload) self.onload(); }, 1);
  };
};

const api = new Function('window', 'document', 'localStorage', 'fetch', 'FileReader',
  script + '\nreturn { STATE: STATE, pick: pick, saveDraft: saveDraft, loadDraft: loadDraft, ' +
  'renderReport: renderReport, dropDraft: dropDraft };')(
  window, document, localStorage, global.fetch, global.FileReader);

let fail = 0;
function ok(name, cond, extra) {
  if (!cond) fail++;
  console.log((cond ? '[OK] ' : '[FAIL] ') + name + (extra ? '  ' + extra : ''));
}
function wait(ms) {
  return new Promise(function (r) { realSetTimeout(r, ms || 30); });
}

(async function () {
  // 1. 作业文件 → /style
  api.pick({ files: [{ name: '热膨胀系数.docx', size: 1558039, fake: 'data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,UEsDBAoAAAAAAA==' }] }, 'up-hw', 'fn-hw');
  await wait(40);
  ok('作业走 /style 接口', !!(lastReq && lastReq.url.indexOf('/style') >= 0), lastReq && lastReq.url);
  ok('上传的是 docx 的 base64', !!(lastReq && lastReq.body && String(lastReq.body.docx_b64).indexOf('UEsD') === 0));
  ok('风格卡写进 STATE', !!(api.STATE.style && /约 9000 字/.test(api.STATE.style.summary || '')), api.STATE.style && api.STATE.style.summary);
  ok('界面显示「读到了」', /读到了/.test(document.getElementById('hw-tip').innerHTML), document.getElementById('hw-tip').innerHTML.slice(0, 40));

  // 2. 截图 → STATE.shotB64
  api.pick({ files: [{ name: 'shot.jpg', size: 237642, fake: 'data:image/jpeg;base64,AAAA' }] }, 'up-shot', 'fn-shot');
  await wait(40);
  ok('截图存成 base64', api.STATE.shotB64 === 'data:image/jpeg;base64,AAAA', String(api.STATE.shotB64));
  ok('截图提示更新', /已就位/.test(document.getElementById('shot-tip').textContent), document.getElementById('shot-tip').textContent);

  // 3. /render 带上截图
  api.STATE.rec = { exp_id: 'photo', tables: { t1: { cells: [[1]] } }, notes: [], meta: { mode: 'mock' } };
  api.renderReport();
  await wait(40);
  const b = lastReq && lastReq.body;
  ok('/render 带上 shot_b64', !!(b && b.shot_b64 === 'AAAA' && b.shot_mime === 'image/jpeg'),
    JSON.stringify(b && { m: b.shot_mime, n: String(b.shot_b64 || '').length }));
  ok('/render 带实验与表格', !!(b && b.exp_id && b.tables), JSON.stringify(b && { e: b.exp_id, t: Object.keys(b.tables || {}) }));

  // 4. 草稿：存 → 清内存 → 读回
  api.STATE.exp = '光电效应的研究';
  api.STATE.files = { data: true, hw: true, shot: true };
  api.saveDraft();
  ok('草稿写进 localStorage', !!store['dsh.draft.v1'], Object.keys(store).join(','));
  api.STATE.rec = null; api.STATE.style = null; api.STATE.files = { data: false, hw: false, shot: false };
  ok('草稿能读回来', api.loadDraft() === true);
  ok('实验名恢复', api.STATE.exp === '光电效应的研究', api.STATE.exp);
  ok('文件勾选恢复', !!(api.STATE.files.data && api.STATE.files.hw && api.STATE.files.shot));
  ok('识别结果恢复', !!(api.STATE.rec && api.STATE.rec.tables));
  ok('风格卡摘要恢复', !!(api.STATE.style && api.STATE.style.summary));

  // 5. 清草稿
  api.dropDraft();
  await wait(10);
  ok('清草稿后 store 里没有', !store['dsh.draft.v1']);
  ok('清草稿后状态清空', api.STATE.rec === null && api.STATE.files.data === false);

  console.log(fail ? '\n[SUM] ' + fail + ' 项失败' : '\n[SUM] 全部通过');
  process.exit(fail ? 1 : 0);
})();
