const fs = require('fs');
const path = 'C:/Users/lidey/Desktop/实验报告制作沙盒/06_网站方案/prototype.html';
const html = fs.readFileSync(path, 'utf8');
const js = html.split('<script>')[1].split('</script>')[0];

const ctx = new Proxy({}, { get:(t,k)=> (k in t ? t[k] : ()=>{}), set:(t,k,v)=>{t[k]=v;return true;} });
const canvas = { width:760, height:520, getContext:()=>ctx, toDataURL:()=>'data:image/png;base64,' };
const el = { innerHTML:'', classList:{toggle(){}, add(){}, remove(){}}, addEventListener(){}, getContext:()=>ctx, click(){} };
global.document = {
  querySelector: (s)=> (s==='#c1'||s==='#c2') ? canvas : el,
  querySelectorAll: ()=>[],
  addEventListener(){}, createElement:()=>el,
};
global.window = global;
global.URL = { createObjectURL:()=>'blob:', revokeObjectURL(){} };
global.Blob = class {};
global.alert = ()=>{};
eval(js);
const D = global.__D;
const r = (v,d=4)=>Number(v).toFixed(d);
console.log('m        =', r(D.main.k,5));
console.log('b        =', r(D.main.b,5));
console.log('r        =', r(D.main.r,6), 'R2=', r(D.main.r2,6));
console.log('lgIs     =', D.rows.map(x=>r(x.lgIs,3)).join(' '));
console.log('phi_eV   =', r(D.phieV,4), ' phi_J=', D.phiJ.toExponential(4));
console.log('relErr % =', r(D.relErr,3), ' u=', r(D.uPhi,4));
console.log('T        =', D.rows.map(x=>x.t).join(' '));
console.log('Y(1/T)   =', D.Y.map(v=>r(v,2)).join(' '));

