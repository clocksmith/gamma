import { createHash } from 'node:crypto';
import { observationWindow } from './observation.mjs';
export const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
export const norm=a=>Math.sqrt(dot(a,a));
export const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
export function rng(seed){let x=seed>>>0;return()=>{x=(Math.imul(x,1664525)+1013904223)>>>0;return x/4294967296;};}
export const counter=()=>({scalarQueries:0,updates:0,clamps:0,skippedCurvature:0,peakStateBytes:0});
export function freeze(value){
 const number=x=>{if(!Number.isFinite(x))throw Error('Nonfinite artifact');const b=Buffer.alloc(8);b.writeDoubleLE(x);return{f64:b.toString('hex')};};
 const encode=x=>typeof x==='number'?number(x)
  :Array.isArray(x)?x.map(encode):x&&typeof x==='object'?Object.fromEntries(Object.entries(x).map(([k,v])=>[k,encode(v)])):x;
 const payload=JSON.stringify(encode(value));
 return JSON.stringify({schema:'gamma.curvature-state/v1',payload,hash:createHash('sha256').update(payload).digest('hex')});
}
export function restore(text){
 const a=JSON.parse(text);
 if(a.schema!=='gamma.curvature-state/v1'||createHash('sha256').update(a.payload).digest('hex')!==a.hash)throw Error('Invalid artifact');
 const number=s=>{if(!/^[0-9a-f]{16}$/.test(s))throw Error('Invalid bytes');const n=Buffer.from(s,'hex').readDoubleLE(0);if(!Number.isFinite(n))throw Error('Nonfinite artifact');return n;};
 const decode=x=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).length===1&&typeof x.f64==='string'
  ?number(x.f64):Array.isArray(x)?x.map(decode)
  :x&&typeof x==='object'?Object.fromEntries(Object.entries(x).map(([k,v])=>[k,decode(v)])):x;
 return decode(JSON.parse(a.payload));
}
export function population(seed,count,family,dimension){
 const random=rng(seed);return Array.from({length:count},(_,j)=>{
  const initial=Array.from({length:dimension},()=>random()*2-1);
  const truth=initial.map(()=>random()*2-1);
  if(family==='quadratic'){
   const blocks=Array.from({length:dimension/2},()=>({angle:random()*Math.PI,high:Math.exp(random()*Math.log(100))}));
   return{id:`${seed}/${family}/${dimension}/${j}`,initial,loss:x=>{
    let loss=0;for(let k=0;k<dimension;k+=2){const b=blocks[k/2],c=Math.cos(b.angle),s=Math.sin(b.angle);
     const u=x[k]-truth[k],v=x[k+1]-truth[k+1],a=c*u+s*v,d=-s*u+c*v;loss+=(a*a+b.high*d*d)/2;}return loss;}};
  }
  const rows=Array.from({length:16},()=>{const x=initial.map(()=>random()*2-1);return{x,y:dot(x,truth)>0?1:-1};});
  return{id:`${seed}/${family}/${dimension}/${j}`,initial,loss:x=>mean(rows.map(row=>{
   const z=-row.y*dot(row.x,x);return Math.max(z,0)+Math.log1p(Math.exp(-Math.abs(z)));}))+0.025*dot(x,x)};
 });
}
function gradient(theta,loss,id,history,seed,budget){
 const window=observationWindow({objectiveId:id,theta,previous:history,loss});
 const random=rng(seed),g=theta.map(()=>0),radius=0.001;
 for(let k=0;k<4;k++){const d=theta.map(()=>random()<0.5?-1:1);
  const p=window.query(theta.map((x,i)=>x+radius*d[i]));
  const m=window.query(theta.map((x,i)=>x-radius*d[i]));
  d.forEach((x,i)=>{g[i]+=(p-m)*x/(8*radius);});}
 budget.scalarQueries+=window.receipt().scalarQueries;return g;
}
function basis(g,step){
 const gn=norm(g);if(gn<1e-12)return null;const u=g.map(x=>x/gn);
 const v=step?step.map((x,i)=>x-dot(step,u)*u[i]):g.map(()=>0),vn=norm(v);
 return{u,v:vn>1e-12?v.map(x=>x/vn):v};
}
export function update({theta,phi,history=null,loss,id,seed,method='learned',rate=0.1,beta=0.9},budget){
 const g=gradient(theta,loss,id,history,seed,budget),n=theta.length;
 const next={objectiveId:id,dimension:n,theta:[...theta],g:[...g],t:(history?.t??0)+1};
 let direction;
 if(method==='adam'){
  next.m=g.map((x,i)=>beta*(history?.m?.[i]??0)+(1-beta)*x);
  next.v=g.map((x,i)=>0.99*(history?.v?.[i]??0)+0.01*x*x);
  direction=g.map((_,i)=>-rate*(next.m[i]/(1-beta**next.t))/(Math.sqrt(next.v[i]/(1-0.99**next.t))+1e-8));
 }else if(method==='bfgs'){
  const pairs=structuredClone(history?.pairs??[]);
  if(history){const s=theta.map((x,i)=>x-history.theta[i]),y=g.map((x,i)=>x-history.g[i]);const sy=dot(s,y);
   if(sy>1e-10*norm(s)*norm(y)&&sy>1e-12){pairs.push({s,y,rho:1/sy});if(pairs.length>2)pairs.shift();}else budget.skippedCurvature++;}
  next.pairs=pairs;let q=[...g];const alpha=[];
  for(let i=pairs.length-1;i>=0;i--){const p=pairs[i];alpha[i]=p.rho*dot(p.s,q);q=q.map((x,j)=>x-alpha[i]*p.y[j]);}
  const last=pairs.at(-1),scale=last?clamp(dot(last.s,last.y)/dot(last.y,last.y),0.001,100):1;
  let r=q.map(x=>scale*x);for(let i=0;i<pairs.length;i++){const p=pairs[i],b=p.rho*dot(p.y,r);r=r.map((x,j)=>x+p.s[j]*(alpha[i]-b));}
  direction=r.map(x=>-rate*x);
 }else{
  if(!Array.isArray(phi)||phi.length!==16||!phi.every(Number.isFinite))throw Error('Invalid rule');
  const step=history?theta.map((x,i)=>x-history.theta[i]):null;
  const previous=history?.g,cos=previous?dot(g,previous)/(norm(g)*norm(previous)+1e-12):0;
  const curvature=step&&previous?dot(step,g.map((x,i)=>x-previous[i]))/(dot(step,step)+1e-12):0;
  const f=[1,Math.tanh(Math.log1p(norm(g))),cos,Math.tanh(curvature)];
  const z=Array.from({length:4},(_,i)=>dot(phi.slice(i*4,i*4+4),f));
  const l1=Math.exp(clamp(z[0],-1,1)),l2=Math.tanh(z[1]),l3=Math.exp(clamp(z[2],-1,1));
  const a=l1*l1,b=l1*l2,c=l2*l2+l3*l3,max=(a+c+Math.sqrt((a-c)**2+4*b*b))/2;
  const aa=0.1+1.9*a/max,bb=1.9*b/max,cc=0.1+1.9*c/max;
  const U=basis(g,step),eta=Math.exp(-4+clamp(z[3],-2,2));
  direction=[...g];if(U){const gu=dot(g,U.u),gv=dot(g,U.v);direction=g.map((x,i)=>x+U.u[i]*((aa-1)*gu+bb*gv)+U.v[i]*(bb*gu+(cc-1)*gv));}
  direction=direction.map(x=>-eta*x);
 }
 const cap=0.25*(1+norm(theta)),dn=norm(direction);
 if(dn>cap){direction=direction.map(x=>x*cap/dn);budget.clamps++;}
 const result=theta.map((x,i)=>x+direction[i]);if(!result.every(Number.isFinite))throw Error('Nonfinite update');
 budget.updates++;budget.peakStateBytes=Math.max(budget.peakStateBytes,Buffer.byteLength(JSON.stringify(next)));
 // Numeric state capacity, not serialized text overhead.
 const count=x=>typeof x==='number'?1:Array.isArray(x)?x.reduce((s,v)=>s+count(v),0):x&&typeof x==='object'?Object.values(x).reduce((s,v)=>s+count(v),0):0;
 if(count(next)>8*n+32)throw Error('State allowance exceeded');
 return{theta:result,history:next};
}
export function utility(phi,tasks,steps,budget){
 return tasks.map(task=>{let state={theta:[...task.initial],history:null};
  for(let step=0;step<steps;step++)state=update({...state,phi,loss:task.loss,id:task.id,seed:50000+step},budget);
  budget.scalarQueries++;return task.loss(state.theta);});
}
