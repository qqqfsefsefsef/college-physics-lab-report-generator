// 检查 prototype_v2.html 的接线：每个 onclick 都能解析到已定义函数/方法
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'prototype_v2.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];

// 1) 语法
try { new Function(script); console.log('[OK] 语法解析通过'); }
catch (e) { console.error('[FAIL] 语法错误: ' + e.message); process.exit(1); }

// 2) 关键函数
const need = ['startGen', 'nextFromApi', 'testConn', 'useDemo', 'togglePwd', 'apiSig',
  'syncGen', 'fillResult', 'buildReview', 'runGen', 'regen', 'doneClean', 'toggleFmt', 'pick'];
const miss = need.filter((n) => !new RegExp('function\\s+' + n + '\\s*\\(').test(script));
if (miss.length) { console.error('[FAIL] 缺函数: ' + miss.join(', ')); process.exit(1); }
console.log('[OK] 关键函数齐全 (' + need.length + ')');

// 3) onclick 目标
const calls = [...html.matchAll(/onclick="([a-zA-Z_$][\w$]*)\(/g)].map((m) => m[1]);
const defined = new Set(need);
for (const m of script.matchAll(/function\s+([a-zA-Z_$][\w$]*)\s*\(/g)) defined.add(m[1]);
for (const m of script.matchAll(/var\s+([a-zA-Z_$][\w$]*)\s*=\s*function/g)) defined.add(m[1]);
const undef = [...new Set(calls)].filter((c) => !defined.has(c));
if (undef.length) { console.error('[FAIL] onclick 调用了未定义函数: ' + undef.join(', ')); process.exit(1); }
console.log('[OK] onclick 目标全部可解析 (' + [...new Set(calls)].length + ' 个): ' +
  [...new Set(calls)].sort().join(', '));

// 4) 关键闸门行为：没填 key 时不再有 disabled 死锁
const apiNext = /id="api-next"[^>]*>/.exec(html);
const dead = apiNext && /disabled/.test(apiNext[0]);
console.log((dead ? '[FAIL] "下一步"仍是 disabled 死锁' : '[OK] "下一步"始终可点（未填 key 时给提示，不卡死）'));
process.exit(dead ? 1 : 0);
