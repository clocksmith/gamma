const assert=require('node:assert/strict'),vm=require('node:vm'),{compile}=require('./compile.cjs');
async function compare(text,args){
 const r=await compile(text);assert.equal(r.skip,null);assert.deepEqual(r.errors,{});assert.equal(Object.keys(r.candidates).length,4);
 function run(src){const context=vm.createContext({});return vm.runInContext(src+';JSON.stringify(solve('+args+'))',context,{timeout:1000});}
 const expected=run(text);for(const src of Object.values(r.candidates))assert.equal(run(src),expected);
}
(async()=>{
 await compare('function solve(a){let b=1;let c=2;if(a)return b+c;return b-c}', 'false');
 await compare('function solve(){let n=0,a={get x(){n++;return 2}};a.x;return [n,a.x,n]}','');
 await compare('function solve(a){let n=0;let f=()=>++n;return [a&&f(),n,a||f(),n]}','false');
 await compare('function solve(a){return [Object.is(a,-0),Number.isNaN(a/a),1/a]}','-0');
 await compare('function solve(a,b){return [arguments.length,a,b]}','1');
 await compare('function solve(a){let b=a;let c=()=>++a[0];c();return [a===b,b[0]]}','[3]');
 const guarded=await compile('function solve(a){return a.toString()}');assert.equal(guarded.skip,'reflection_guard');assert.deepEqual(Object.keys(guarded.candidates),['original']);
 console.log('7 synthetic compiler checks passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
