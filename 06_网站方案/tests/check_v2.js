// 校验 prototype_v2.html：① 内联 JS 能被解析；② compute() 的数值与引擎一致。
// 用法：node tests/check_v2.js   （不 spawn 子进程，避免沙箱 EPERM）
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'prototype_v2.html'), 'utf8');

const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) { console.error('[FAIL] 找不到 <script> 块'); process.exit(1); }
const code = m[1];

// ① 语法解析（new Function 会真正解析一遍）
try {
  new Function(code);
  console.log('[OK] 语法解析通过');
} catch (e) {
  console.error('[FAIL] 语法错误：' + e.message);
  process.exit(1);
}

// ② 跑 compute()，DOM 用桩
const stubEl = () => ({
  classList: { add() {}, remove() {}, contains() { return false; } },
  style: {}, textContent: '', innerHTML: '', value: '', files: null,
  appendChild() {}, setAttribute() {}, getAttribute() { return null; },
  querySelectorAll() { return []; }, addEventListener() {}, children: [],
});
const doc = {
  getElementById: stubEl, querySelectorAll: () => [], querySelector: stubEl,
  createElement: stubEl, addEventListener() {},
};
const win = { scrollTo() {} };
const ls = { getItem: () => null, setItem() {}, removeItem() {} };

const factory = new Function('document', 'window', 'localStorage', code + '\nreturn {compute: compute};');
const api = factory(doc, win, ls);
const r = api.compute();

const checks = [
  ['Nbar/cm', r.Nbar, 11.1288, 1e-3],
  ['S/cm', r.S, 0.0063, 5e-4],
  ['d/mm', r.d, 0.298, 5e-4],
  ['F/N', r.F, 39.176, 1e-6],
  ['Y/Pa', r.Y, 2.0166e11, 2e8],
  ['u(Y)/Y %', r.rel, 2.84, 0.03],
];
let bad = 0;
for (const c of checks) {
  const ok = Math.abs(c[1] - c[2]) <= c[3];
  if (!ok) bad++;
  console.log((ok ? '[OK]   ' : '[FAIL] ') + c[0] + ': ' + c[1] + ' (期望 ' + c[2] + ' ±' + c[3] + ')');
}
console.log('[SUM] ' + (checks.length - bad) + '/' + checks.length + ' 通过；Y = ' +
  (r.Y / 1e11).toFixed(4) + 'x1e11 Pa, u/Y = ' + r.rel.toFixed(3) + '%');
process.exit(bad ? 1 : 0);
