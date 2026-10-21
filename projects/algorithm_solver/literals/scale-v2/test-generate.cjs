const assert = require('node:assert/strict'), vm = require('node:vm');
const {compact, normalize, canonical} = require('./generate.cjs');
const cases = [
  ['function solve(x){const a=3;return x.map(a=>({a,x:a+x.length})).concat(a)}', [[1,2,3]]],
  ['function solve(n){function f(n){return n<2?1:n*f(n-1)}return f(n)}', [5]],
  ['class Box{constructor(x){this.x=x}value(){return this.x}}function solve(x){return new Box(x).value()}', [7]],
  ['function solve(x){let a=0;for(const y of x)a+=y;return a}', [[2,4,6]]],
  ['function solve(x){let a="a";return {a,value:x}+a}', [2]],
  ['function solve(x){const a=2;return x.map(y=>()=>y+a).map(f=>f())}', [[2,3]]],
];
for (const [text,args] of cases) {
  const run = code => vm.runInNewContext(code+';JSON.stringify(solve(...'+JSON.stringify(args)+'))');
  assert.equal(run(compact(text)),run(text));
  assert.equal(run(compact(canonical(text))),run(text));
}
assert.throws(()=>compact('function solve(x){return eval(x)}'));
const n = normalize('function recurse(n){return n<2?1:n*recurse(n-1)}');
assert.equal(vm.runInNewContext(n.source+';solve(5)'),120);
assert.equal(n.entry,'recurse');
console.log('15 binding, closure, class alias, property, recursion, reflection and entrypoint assertions passed');
