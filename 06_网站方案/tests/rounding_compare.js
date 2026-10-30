const UA=[25,36,49,64,81,100,121,144];
const IF=[0.600,0.625,0.650,0.675,0.700,0.725,0.750,0.775];
const IA=[[23,23,24,24,25,26,26,28],[43,44,44,45,46,48,48,50],[78,80,81,83,84,86,87,88],
[139,140,142,143,152,152,153,157],[237,242,244,249,255,260,262,268],[393,405,410,420,425,434,447,431],
[645,664,666,682,694,707,725,728],[1030,1050,1071,1081,1112,1129,1144,1162]];
const lg=x=>Math.log10(x), T=i=>920+1600*IF[i];
function lsq(xs,ys){const n=xs.length,mx=xs.reduce((a,b)=>a+b)/n,my=ys.reduce((a,b)=>a+b)/n;let sxx=0,sxy=0,syy=0;
for(let i=0;i<n;i++){const dx=xs[i]-mx,dy=ys[i]-my;sxx+=dx*dx;sxy+=dx*dy;syy+=dy*dy;}
const k=sxy/sxx;let sse=0;for(let i=0;i<n;i++){const r=ys[i]-(k*xs[i]+(my-k*mx));sse+=r*r;}
return {k,b:my-k*mx,r:sxy/Math.sqrt(sxx*syy)};}
const K=1.380649e-23,E=1.602176634e-19;
function run(roundTable){
  const lgis=[],Tv=[];
  IF.forEach((f,i)=>{
    Tv.push(T(i));
    let ys=IA[i].map(v=>lg(v));
    if(roundTable) ys=ys.map(v=>+v.toFixed(2));
    lgis.push(lsq(UA.map(Math.sqrt),ys).b);
  });
  let X=Tv.map(t=>1000/t), Y=lgis.map((v,i)=>v-2*lg(Tv[i]/1000));
  if(roundTable){X=X.map(v=>+v.toFixed(2)); Y=Y.map(v=>+v.toFixed(2));}
  const f=lsq(X,Y), mTrue=f.k*1000, phi=2.303*K*Math.abs(mTrue)/E;
  return {m:f.k,b:f.b,r:f.r,phi,lgis:lgis.map(v=>v.toFixed(3)),Y:Y.map(v=>v.toFixed(2))};
}
for (const rt of [false,true]) {
  const o=run(rt);
  console.log('roundTable='+rt, 'm='+o.m.toFixed(3), 'b='+o.b.toFixed(3), 'r='+o.r.toFixed(5),
              'phi='+o.phi.toFixed(3), 'E='+((o.phi-4.54)/4.54*100).toFixed(2)+'%');
  console.log('   lgIs:', o.lgis.join(' '));
  console.log('   Y   :', o.Y.join(' '));
}
