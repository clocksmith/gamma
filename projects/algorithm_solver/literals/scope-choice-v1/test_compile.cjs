const assert=require('node:assert/strict'),vm=require('node:vm'),{compile,nth,orders}=require('./compile.cjs');
async function compare(text,args){
 const r=await compile(text);assert.equal(r.skip,null);assert.deepEqual(r.errors,{});assert.equal(Object.keys(r.candidates).length,12);
 const run=src=>vm.runInNewContext(src+';JSON.stringify(solve('+args+'))',{},{timeout:1000});
 const expected=run(text);for(const src of Object.values(r.candidates))assert.equal(run(src),expected);return r;
}
(async()=>{
 const a=await compare('function solve(input){function first(longOne){return longOne+1}function second(longTwo){return longTwo*2}return first(input)+second(input)}','3');
 assert(a.binding_stats.rotate00.distinct_spellings<a.binding_stats.original.distinct_spellings);
 await compare('function solve(outer){let hold=outer+1;return [1,2].map(inner=>inner+hold+outer)}','5');
 await compare('function solve(input){let answer=[];for(let index=0;index<3;index++)answer.push(()=>index+input);return answer.map(f=>f())}','4');
 await compare('function solve(input){let value=input+1;return {value,input}}','3');
 await compare('function solve(input){let result=[];try{throw input}catch(caught){result.push(caught)}return result}','7');
 await compare('function solve(a,b){return [arguments.length,a,b]}','1');
 await compare('function solve(input){return Math.max(input,3)}','2');
 const guarded=await compile('function solve(x){return eval("x")}');assert.equal(guarded.skip,'reflection_guard');
 const words=Array.from({length:3000},(_,n)=>nth(orders.rotate00).get(n));assert.equal(new Set(words).size,words.length);assert(words.every(x=>/^[a-z]+$/.test(x)));
 console.log('9 scope/naming synthetic checks passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
