'use strict';
const fs=require('fs'),vm=require('vm');
function decode(x){
 if(Array.isArray(x))return x.map(decode);if(x===null||typeof x!=='object')return x;
 if(Object.keys(x).length===1&&Array.isArray(x.__list_node__)){let head=null;for(const v of x.__list_node__.slice().reverse())head={val:v,next:head};return head;}
 if(Object.keys(x).length===1&&Array.isArray(x.__tree_node__)){const a=x.__tree_node__;if(!a.length||a[0]===null)return null;const root={val:a[0],left:null,right:null},q=[root];let i=1;for(let k=0;k<q.length&&i<a.length;k++)for(const key of ['left','right']){if(i<a.length&&a[i]!==null){q[k][key]={val:a[i],left:null,right:null};q.push(q[k][key]);}i++;}return root;}
 return Object.fromEntries(Object.entries(x).map(([k,v])=>[k,decode(v)]));
}
function encode(x){
 if(typeof x==='bigint')return {__gamma_bigint_v1__:x.toString()};
 if(typeof x==='number'&&(!Number.isFinite(x)||(Number.isInteger(x)&&!Number.isSafeInteger(x))))throw Error('Unsafe numeric output');
 if(Array.isArray(x))return x.map(encode);if(x===null||typeof x!=='object')return x;
 if('val' in x && 'next' in x){let a=[],seen=new Set();for(let p=x;p!==null;p=p.next){if(seen.has(p)||a.length>10000)throw Error('Invalid list');seen.add(p);a.push(encode(p.val));}return {__list_node__:a};}
 if('val' in x && 'left' in x && 'right' in x){let a=[],q=[x],seen=new Set();for(let k=0;k<q.length;k++){let p=q[k];if(p===null){a.push(null);continue;}if(seen.has(p)||q.length>20000)throw Error('Invalid tree');seen.add(p);a.push(encode(p.val));q.push(p.left,p.right);}while(a.at(-1)===null)a.pop();return {__tree_node__:a};}
 return Object.fromEntries(Object.entries(x).map(([k,v])=>[k,encode(v)]));
}
function aliases(args,result){
 const seen=new WeakMap(),edges=[],stack=[[result,['result',null]],[args,['args',null]]];
 function render(p){const parts=[];while(p!==null){parts.push(p[0]);p=p[1];}return parts.reverse().join('.');}
 while(stack.length){
  const[v,p]=stack.pop();if(v===null||typeof v!=='object')continue;
  if(seen.has(v)){edges.push([render(p),render(seen.get(v))]);continue;}
  seen.set(v,p);
  // Preserve Object.entries' eager getter/Proxy order and value snapshot.
  const entries=Object.entries(v);
  for(let i=entries.length-1;i>=0;i--){
   const child=entries[i][1];
   if(child!==null&&typeof child==='object')stack.push([child,[entries[i][0],p]]);
  }
 }
 return edges;
}
function main(){const p=JSON.parse(fs.readFileSync('inputs.json'));vm.runInThisContext(fs.readFileSync('program.js','utf8'),{timeout:1000});const target=vm.runInThisContext(p.entry);for(let i=0;i<p.calls.length;i++){const args=decode(p.calls[i].args);let record;try{const before=encode(args),result=target(...args);record={i,result:encode(result),result_type:typeof result,args_before:before,args_after:encode(args),alias_edges:aliases(args,result)};}catch(e){record={i,error:String(e)};}process.stdout.write(JSON.stringify(record)+'\n');}process.stdout.write(JSON.stringify({done:p.calls.length})+'\n');}
if(require.main===module)main();module.exports={decode,encode,aliases};
