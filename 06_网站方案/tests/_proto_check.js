
/* ================= 数据 ================= */
const UA = [25,36,49,64,81,100,121,144];
const IF = [0.600,0.625,0.650,0.675,0.700,0.725,0.750,0.775];
const IA = [
  [23,23,24,24,25,26,26,28],
  [43,44,44,45,46,48,48,50],
  [78,80,81,83,84,86,87,88],
  [139,140,142,143,152,152,153,157],
  [237,242,244,249,255,260,262,268],
  [393,405,410,420,425,434,447,431],
  [645,664,666,682,694,707,725,728],
  [1030,1050,1071,1081,1112,1129,1144,1162],
];
const K_B = 1.380649e-23, E_C = 1.602176634e-19, LN10 = 2.303, PHI_ACCEPT = 4.54;

/* ================= 数学 ================= */
const lg = x => Math.log10(x);
const T = i => 920 + 1600 * IF[i];

function lsq(xs, ys){                       // 最小二乘 + 相关 + 斜率标准偏差
  const n = xs.length;
  const mx = xs.reduce((a,b)=>a+b,0)/n, my = ys.reduce((a,b)=>a+b,0)/n;
  let sxx=0, sxy=0, syy=0;
  for (let i=0;i<n;i++){ const dx=xs[i]-mx, dy=ys[i]-my; sxx+=dx*dx; sxy+=dx*dy; syy+=dy*dy; }
  const k = sxy/sxx, b = my - k*mx;
  let sse = 0;
  for (let i=0;i<n;i++){ const r = ys[i]-(k*xs[i]+b); sse += r*r; }
  const se = Math.sqrt(sse/(n-2))/Math.sqrt(sxx);
  const r = syy>0 ? sxy/Math.sqrt(sxx*syy) : 0;
  return {k, b, r, r2:r*r, se};
}

function compute(){
  // 与手工流程一致：表里写几位就算几位（表 2 保留 2 位小数、表 3 的 1/T 与 lg(I_s/T²) 各 2 位）
  const rows = IF.map((ifv,i) => {
    const t = T(i);
    const xs = UA.map(u => Math.sqrt(u));
    const ys = IA[i].map(v => +lg(v).toFixed(2));
    const f = lsq(xs, ys);
    return {ifv, t, xs, ys, k:f.k, b:f.b, r:f.r, lgIs:f.b};
  });
  const X = rows.map(r => +(1000/r.t).toFixed(2));            // 1/T，单位 10⁻³K⁻¹
  const Y = rows.map(r => +(r.lgIs - 2*lg(r.t/1000)).toFixed(2)); // lg I_s − 2lg(T/10³)
  const main = lsq(X, Y);
  const mTrue = main.k * 1000;
  const phiJ = LN10 * K_B * Math.abs(mTrue);
  const phieV = phiJ / E_C;
  const uPhi = LN10 * K_B * main.se * 1000 / E_C;
  return {rows, X, Y, main, mTrue, phiJ, phieV, uPhi, relErr:(phieV-PHI_ACCEPT)/PHI_ACCEPT*100};
}

/* ================= 渲染 ================= */
const fmt = (v,d=3) => v.toFixed(d).replace('-','−');
const $ = s => document.querySelector(s);

function renderTables(D){
  // 表 1（可编辑）
  let h = '<tr><th rowspan="2" style="min-width:56px">I<sub>f</sub> / A</th>' +
          '<th colspan="8" style="text-align:center">U<sub>a</sub> / V</th></tr><tr>' +
          UA.map(u=>'<th>'+u+'</th>').join('') + '</tr>';
  IF.forEach((ifv,i)=>{
    h += '<tr><th>'+ifv.toFixed(3)+'</th>';
    IA[i].forEach((v,j)=>{
      h += '<td><input data-i="'+i+'" data-j="'+j+'" value="'+v+'" inputmode="numeric"></td>';
    });
    h += '</tr>';
  });
  $('#t1').innerHTML = h;

  // 表 2（lg I_a）
  let h2 = '<tr><th rowspan="2">T / 10³K</th><th colspan="8" style="text-align:center">√U<sub>a</sub></th></tr><tr>' +
           UA.map(u=>'<th>'+Math.sqrt(u).toFixed(1)+'</th>').join('') + '</tr>';
  D.rows.forEach(r=>{
    h2 += '<tr><th>'+r.t.toFixed(3).slice(0,4)+'</th>' + r.ys.map(v=>'<td>'+v.toFixed(2)+'</td>').join('') + '</tr>';
  });
  $('#t2').innerHTML = h2;

  // 表 3
  let h3 = '<tr><th>T / 10³K</th>' + D.rows.map(r=>'<th>'+(r.t/1000).toFixed(2)+'</th>').join('') + '</tr>';
  h3 += '<tr><th>1/T (10⁻³K⁻¹)</th>' + D.X.map(v=>'<td>'+v.toFixed(2)+'</td>').join('') + '</tr>';
  h3 += '<tr><th>lg I<sub>s</sub></th>' + D.rows.map(r=>'<td>'+r.lgIs.toFixed(3)+'</td>').join('') + '</tr>';
  h3 += '<tr><th>lg(I<sub>s</sub>/T²)</th>' + D.Y.map(v=>'<td>'+v.toFixed(2)+'</td>').join('') + '</tr>';
  $('#t3').innerHTML = h3;
}

function renderKPI(D){
  const e = D.relErr;
  $('#kpis').innerHTML = [
    ['斜率 m（10⁻³K⁻¹）', fmt(D.main.k,3), ''],
    ['相关系数 r', fmt(D.main.r,4), 'R²=' + D.main.r2.toFixed(4)],
    ['逸出功 eφ', fmt(D.phieV,2)+' eV', fmt(D.phiJ*1e19,2)+'×10⁻¹⁹ J'],
    ['相对误差', (e>0?'+':'')+fmt(e,2)+'%', '公认 4.54 eV'],
  ].map(([k,v,u])=>'<div class="kpi"><div class="k">'+k+'</div><div class="v'+(k==='相对误差'?' ok':'')+'">'+v+
      '</div><div class="u">'+u+'</div></div>').join('');
  $('#dataNote').innerHTML = '截距 lg I<sub>s</sub> = ' + D.rows.map(r=>r.lgIs.toFixed(2)).join(' / ') +
      '；m = ' + fmt(D.main.k,3) + '、b = ' + fmt(D.main.b,3) + '；u(eφ) = ' + D.uPhi.toFixed(3) + ' eV。';
}

/* ---------- 画图（不依赖任何图表库，方便复刻论文式样） ---------- */
function axes(ctx,W,H,pad,xr,yr,xt,yt,xlab,ylab,title){
  ctx.clearRect(0,0,W,H);
  ctx.font='16px "Microsoft YaHei",sans-serif'; ctx.fillStyle='#1b1f24'; ctx.textAlign='center';
  ctx.fillText(title,W/2,30);
  const X = v => pad.l + (v-xr[0])/(xr[1]-xr[0])*(W-pad.l-pad.r);
  const Y = v => H-pad.b - (v-yr[0])/(yr[1]-yr[0])*(H-pad.t-pad.b);
  // 网格
  ctx.strokeStyle='#eef1f5'; ctx.lineWidth=1;
  for(let v=Math.ceil(xr[0]/xt)*xt; v<=xr[1]; v+=xt){ ctx.beginPath(); ctx.moveTo(X(v),Y(yr[0])); ctx.lineTo(X(v),Y(yr[1])); ctx.stroke(); }
  for(let v=Math.ceil(yr[0]/yt)*yt; v<=yr[1]; v+=yt){ ctx.beginPath(); ctx.moveTo(X(xr[0]),Y(v)); ctx.lineTo(X(xr[1]),Y(v)); ctx.stroke(); }
  // 坐标轴
  ctx.strokeStyle='#1b1f24'; ctx.lineWidth=1.4;
  ctx.beginPath(); ctx.moveTo(X(xr[0]),Y(yr[0])); ctx.lineTo(X(xr[1]),Y(yr[0]));
  ctx.moveTo(X(xr[0]),Y(yr[0])); ctx.lineTo(X(xr[0]),Y(yr[1])); ctx.stroke();
  // 刻度
  ctx.font='12px "Microsoft YaHei",sans-serif'; ctx.fillStyle='#5a6472';
  ctx.textAlign='center'; ctx.textBaseline='top';
  for(let v=Math.ceil(xr[0]/xt)*xt; v<=xr[1]+1e-9; v+=xt){
    ctx.fillText(Math.abs(v)<1e-9?'0':(xt<1?v.toFixed(2):v), X(v), Y(yr[0])+6);
  }
  ctx.textAlign='right'; ctx.textBaseline='middle';
  for(let v=Math.ceil(yr[0]/yt)*yt; v<=yr[1]+1e-9; v+=yt){
    ctx.fillText(yt<1?v.toFixed(1):v.toFixed(1), X(xr[0])-8, Y(v));
  }
  // 轴标题
  ctx.font='14px "Microsoft YaHei",sans-serif'; ctx.fillStyle='#1b1f24';
  ctx.textAlign='center'; ctx.textBaseline='top';
  ctx.fillText(xlab, W/2, H-26);
  ctx.save(); ctx.translate(20,H/2); ctx.rotate(-Math.PI/2); ctx.fillText(ylab,0,0); ctx.restore();
  return {X,Y};
}

function drawFamily(cv, D){
  const ctx = cv.getContext('2d'), W = cv.width, H = cv.height;
  const {X,Y} = axes(ctx,W,H,{l:64,r:22,t:52,b:46},[0,12.5],[1.2,3.2],2,0.2,'√U_a','lg I_a','各温度下 lg I_a – √U_a 直线族');
  const colors=['#555','#d95c5c','#3b7dd8','#2f9e6f','#c88a2e','#8a5cd0','#22a6b3','#777'];
  D.rows.forEach((r,i)=>{
    // 拟合直线：外延到 x=0
    ctx.strokeStyle=colors[i]; ctx.lineWidth=1.3; ctx.beginPath();
    ctx.moveTo(X(0),Y(r.k*0+r.b)); ctx.lineTo(X(12),Y(r.k*12+r.b)); ctx.stroke();
    // 数据点
    ctx.fillStyle=colors[i];
    r.xs.forEach((x,j)=>{ ctx.beginPath(); ctx.arc(X(x),Y(r.ys[j]),3.2,0,7); ctx.fill(); });
    // 截距标记
    ctx.fillStyle=colors[i]; ctx.beginPath();
    ctx.moveTo(X(0),Y(r.b)-5); ctx.lineTo(X(0)+5,Y(r.b)); ctx.lineTo(X(0),Y(r.b)+5); ctx.lineTo(X(0)-5,Y(r.b)); ctx.fill();
    // 右侧温度标签
    ctx.font='12px "Microsoft YaHei",sans-serif'; ctx.fillStyle='#5a6472'; ctx.textAlign='left'; ctx.textBaseline='middle';
    ctx.fillText((r.t/1000).toFixed(2), X(12.1), Y(r.b + r.k*12));
  });
}

function drawMain(cv, D){
  const ctx = cv.getContext('2d'), W = cv.width, H = cv.height;
  const {X,Y} = axes(ctx,W,H,{l:74,r:22,t:52,b:46},[0.45,0.54],[0.6,3.0],0.01,0.2,'1/T (10⁻³ K⁻¹)','lg( I_s / T² )','lg( I_s / T² ) – 1/T 直线');
  ctx.strokeStyle='#2f6feb'; ctx.lineWidth=1.6; ctx.beginPath();
  ctx.moveTo(X(0.45),Y(D.main.k*0.45+D.main.b)); ctx.lineTo(X(0.54),Y(D.main.k*0.54+D.main.b)); ctx.stroke();
  D.rows.forEach((r,i)=>{
    ctx.fillStyle='#c0392b'; ctx.beginPath(); ctx.arc(X(D.X[i]),Y(D.Y[i]),4,0,7); ctx.fill();
    ctx.font='11.5px "Microsoft YaHei",sans-serif'; ctx.fillStyle='#5a6472'; ctx.textAlign='left';
    ctx.fillText((r.t/1000).toFixed(2), X(D.X[i])+7, Y(D.Y[i])-5);
  });
  // 参数框
  const txt = ['m = ' + fmt(D.main.k,3), 'b = ' + fmt(D.main.b,3), 'r = ' + fmt(D.main.r,4),
               'eφ = ' + fmt(D.phieV,2) + ' eV', 'E = ' + fmt(D.relErr,2) + ' %'];
  ctx.fillStyle='rgba(255,255,255,.94)'; ctx.strokeStyle='#c9d1dc'; ctx.lineWidth=1;
  ctx.beginPath(); ctx.rect(W-232, 62, 212, 118); ctx.fill(); ctx.stroke();
  ctx.font='12.5px "Microsoft YaHei",sans-serif'; ctx.fillStyle='#1b1f24'; ctx.textAlign='left'; ctx.textBaseline='middle';
  txt.forEach((s,i)=>ctx.fillText(s, W-220, 84+i*23));
}

/* ================= 打印报告 ================= */
function renderSheet(D){
  const cap = (s)=>'<p class="cap">'+s+'</p>';
  let shot1 = '', shot2 = '';
  try { shot1 = $('#c1').toDataURL('image/png'); shot2 = $('#c2').toDataURL('image/png'); } catch(e){}  // 打印时带上真图
  const t1 = '<table><tr><th rowspan="2">I_f / A</th><th colspan="8">U_a / V</th></tr><tr>' +
    UA.map(u=>'<th>'+u+'</th>').join('')+'</tr>' +
    IF.map((v,i)=>'<tr><th>'+v.toFixed(3)+'</th>'+IA[i].map(x=>'<td>'+x+'</td>').join('')+'</tr>').join('') + '</table>';
  const t3 = '<table><tr><th>T / 10³K</th>'+D.rows.map(r=>'<th>'+(r.t/1000).toFixed(2)+'</th>').join('')+'</tr>' +
    '<tr><th>1/T (10⁻³K⁻¹)</th>'+D.X.map(v=>'<td>'+v.toFixed(2)+'</td>').join('')+'</tr>' +
    '<tr><th>lg I_s</th>'+D.rows.map(r=>'<td>'+r.lgIs.toFixed(3)+'</td>').join('')+'</tr>' +
    '<tr><th>lg(I_s/T²)</th>'+D.Y.map(v=>'<td>'+v.toFixed(2)+'</td>').join('')+'</tr></table>';
  const fig = (src,capText)=> src ? '<img class="fig" src="'+src+'" style="width:86%">'+cap(capText) : cap(capText);

  $('#sheet').innerHTML =
    '<h1>钨的逸出功测定</h1>' +
    '<div class="meta">自动化　院　机器人工程　专业　2025　年级　一　班　　学号 202583240016　姓名 李得源　指导教师 周凯</div>' +
    '<h3>【数据处理及结果】</h3>' +
    '<p>表 1　不同灯丝电流 I_f 和阳极电压 U_a 对应的阳极电流 I_a 值</p>' + t1 +
    '<p>表 2　不同温度 T 和 √U_a 下对应的阳极电流的对数值 lg I_a（见页面交互表）</p>' +
    fig(shot1, '图 4　lg I_a–√U_a 拟合直线族（外延到 √U_a = 0 求 lg I_s）') +
    '<p>表 3　lg(I_s/T²)～1/T 数据表</p>' + t3 +
    fig(shot2, '图 5　lg(I_s/T²)–1/T 直线（斜率求逸出功）') +
    '<p>拟合得斜率 m = ' + fmt(D.main.k,3) + '，截距 b = ' + fmt(D.main.b,3) +
      '，r = ' + fmt(D.main.r,4) + '。由 eφ = 2.303k|m| 得 eφ = ' + fmt(D.phieV,2) +
      ' eV，与公认值 4.54 eV 相比相对误差 ' + fmt(D.relErr,2) + '%。</p>';
}

/* ================= 交互 ================= */
function refresh(){
  const D = compute();
  renderTables(D); renderKPI(D);
  drawFamily($('#c1'), D); drawMain($('#c2'), D);
  renderSheet(D);
  window.__D = D;
}

document.addEventListener('input', e=>{
  const el = e.target;
  if (el.matches('#t1 input')){
    const i = +el.dataset.i, j = +el.dataset.j;
    const v = parseFloat(String(el.value).replace(/[^0-9.\-]/g,''));
    IA[i][j] = isFinite(v) && v > 0 ? v : IA[i][j];
    refresh();
  }
});

$('#nav').addEventListener('click', e=>{
  const b = e.target.closest('button'); if (!b) return;
  document.querySelectorAll('#nav button').forEach(x=>x.classList.toggle('on', x===b));
  ['p1','p2','p3','p4'].forEach((id,k)=>$('#'+id).classList.toggle('hidden', String(k+1)!==b.dataset.t));
});

function exportJSON(){
  const D = window.__D;
  const payload = {
    experiment: 'tungsten-work-function',
    tables: {Ua: UA, If: IF, Ia: IA},
    derived: {
      T: D.rows.map(r=>r.t), invT: D.X, lgIs: D.rows.map(r=>r.lgIs), lgIsT2: D.Y,
      fit: {m: D.main.k, b: D.main.b, r: D.main.r},
      result: {phi_eV: D.phieV, relErr: D.relErr, u_eV: D.uPhi},
    },
  };
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)], {type:'application/json'}));
  a.download = 'tungsten-work-function.json'; a.click();
  URL.revokeObjectURL(a.href);
}

/* ================= ⓪ 输出格式：最先选，决定导出按钮 ================= */
const FMT = [
  {id:'pdf',  name:'PDF 提交版',   desc:'交作业用的就是它：版式固定、不可改、文字可检索', tag:'推荐'},
  {id:'docx', name:'Word 可编辑版', desc:'要自己改体会、答辩前再改内容时用', tag:''},
  {id:'json', name:'数据 JSON',     desc:'留档、复现，下次微调不用重录数据', tag:''},
  {id:'png',  name:'图表 PNG',      desc:'贴 PPT 或答辩用，单张导出', tag:''},
];
let OUT = null;
try { OUT = JSON.parse(localStorage.getItem('fmt') || 'null'); } catch(e){ OUT = null; }
if (!OUT || typeof OUT !== 'object') OUT = {pdf:true, docx:true, json:false, png:false};

function renderOut(){
  const box = $('#outBtns'); if (!box) return;
  const B = [];
  if (OUT.pdf)  B.push('<button class="btn primary" onclick="window.print()">打印 / 导出 PDF</button>');
  if (OUT.docx) B.push('<button class="btn" onclick="alert(\'M2：用 docx.js 在浏览器里直出 宋体 12pt / #494949 的 .docx\')">导出 .docx（M2）</button>');
  if (OUT.json) B.push('<button class="btn" onclick="exportJSON()">导出数据 JSON</button>');
  if (OUT.png)  B.push('<button class="btn" onclick="alert(\'M2：两张图各存一份 PNG\')">导出图表 PNG（M2）</button>');
  box.innerHTML = B.join('') || '<span style="color:#c00">请回到第 ① 步选择输出格式</span>';
  const tip = ['PDF 由浏览器打印生成，A4 边距 上/下 25.4mm、左/右 31.7mm 已按模板设好。'];
  if (OUT.pdf) tip.push('打印时把对话框里的「页眉和页脚」勾掉——页眉页脚由报告样式自己控制。');
  if (OUT.docx && !OUT.pdf) tip.push('只出 Word 版的话，交作业前记得自己另存一份 PDF。');
  if (!OUT.docx) tip.push('没选 Word 版：以后想改内容只能整份重新生成。');
  $('#outNote').textContent = tip.join(' ');
}

function renderFmt(){
  $('#fmtCards').innerHTML = FMT.map(f=>{
    const on = !!OUT[f.id];
    return '<label style="flex:1 1 200px;min-width:190px;cursor:pointer;border:2px solid ' + (on?'#1d4ed8':'#d5dbe3') +
      ';background:' + (on?'#eef3ff':'#fff') + ';border-radius:10px;padding:10px 12px;display:block">' +
      '<input type="checkbox" data-f="' + f.id + '"' + (on?' checked':'') + ' style="margin-right:6px">' +
      '<b style="font-size:13px">' + f.name + '</b>' +
      (f.tag ? '<span style="font-size:11px;color:#1d4ed8;margin-left:6px">' + f.tag + '</span>' : '') +
      '<div style="font-size:12px;color:#5a6472;margin-top:4px;line-height:1.45">' + f.desc + '</div></label>';
  }).join('');
  const picked = FMT.filter(f=>OUT[f.id]).map(f=>f.name);
  $('#fmtNote').textContent = picked.length
    ? '本次将产出：' + picked.join(' + ') + '　·　内容只生成一次，格式只是渲染，勾几个都不涨价。'
    : '还没选：至少要 PDF 或 Word 之一，否则没法交作业。';
  renderOut();
}

document.addEventListener('change', e=>{
  const el = e.target;
  if (el.matches('#fmtCards input[data-f]')){
    OUT[el.dataset.f] = el.checked;
    try { localStorage.setItem('fmt', JSON.stringify(OUT)); } catch(err){}
    renderFmt();
  }
});
renderFmt();

refresh();
