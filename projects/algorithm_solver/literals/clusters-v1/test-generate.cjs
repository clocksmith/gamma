const assert=require('node:assert/strict'),vm=require('node:vm'),{normal,canonical,features}=require('./generate.cjs');
const sources=[
 'function sum(a){let b=0;for(const c of a)b+=c;return b;}class Solution{run(x){return sum(x);}}',
 'function f(a){return a.map((b)=>({b,a:b+a.length}));}class Solution{run(x){return f(x);}}',
 'function f(a){return a<=1?1:a*f(a-1);}class Solution{run(x){return f(x);}}',
 'class Solution{run(x){const value=3;return x.map(value=>value+1).concat(value);}}'
];
for(let i=0;i<sources.length;i++){const n=normal(sources[i]),c=canonical(n.source),arg=i===2?5:[1,2,3];const a=vm.runInNewContext(n.source+';JSON.stringify(solve('+JSON.stringify(arg)+'))');const b=vm.runInNewContext(c.source+';JSON.stringify(solve('+JSON.stringify(arg)+'))');assert.equal(a,b);assert(features(c.source).fragments.every(x=>c.source.includes(x)));}
assert.throws(()=>normal('class Solution{run(){return this.x;}}'));
assert.throws(()=>normal('class Solution{a(){} b(){}}'));
console.log('10 guarded normalization/capture/shorthand/recursion/fragment checks passed');
