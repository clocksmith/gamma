"use strict";
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const h=vm.runInNewContext(fs.readFileSync(__dirname+'/row.js','utf8')+'\nh');
function full(a,b,c,d){
 const rows=Array.from({length:a+1},()=>new Array(b+1));
 for(let i=0;i<=a;i++)for(let j=0;j<=b;j++){
  rows[i][j]=i===0?c(0,j,j?rows[0][j-1]:undefined):j===0?c(i,0,rows[i-1][0]):d(i,j,rows[i-1][j],rows[i][j-1],rows[i-1][j-1]);
 }
 return rows[a][b];
}
const modes=[
 [(i,j,p)=>1n,(i,j,u,l,d)=>u+l],
 [(i,j,p)=>i+j,(i,j,u,l,d)=>1+Math.min(u,l,d)],
 [(i,j,p)=>i+j===0||Boolean(p),(i,j,u,l,d)=>((i+j)%3!==1)&&(u||l)],
 [(i,j,p)=>i+j===1?0:Infinity,(i,j,u,l,d)=>i+j+Math.min(u,l)]
];
let cases=0;
for(let a=0;a<=6;a++)for(let b=0;b<=6;b++)for(const [boundary,step]of modes){
 assert.strictEqual(h(a,b,boundary,step),full(a,b,boundary,step));cases++;
}
const boundary=(i,j,p)=>i+j,diag=(i,j,u,l,d)=>(i===j?d:1+Math.min(u,l,d));
assert.strictEqual(h(2,2,boundary,diag),0);cases++;
assert.notStrictEqual(h(2,2,boundary,(i,j,u,l,d)=>i===j?u:1+Math.min(u,l,d)),0);cases++;
console.log(JSON.stringify({checks:cases,passed:cases,scope:'Full-matrix oracle, scalar/BigInt/Boolean boundaries, zero dimensions and diagonal counterexample'}));
