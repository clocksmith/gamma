const assert=require('node:assert/strict'),{functional,arrow,fragments}=require('./generate.cjs');
const source='function solve(values) { const counts=new Map(); for(const value of values) counts.set(value,(counts.get(value)||0)+1); return counts.size; }';
assert.equal(functional(source).status,'rewritten');assert.equal(functional(source.replace('||0)+1','||0)+2')).status,'unsupported');assert.equal(functional(source.replace('values) {','Array) {')).status,'unsupported');
assert.equal(arrow('function solve(values) { return this.x; }').status,'unsupported');assert.equal(arrow('function solve(values) { return solve(values); }').status,'unsupported');assert.equal(arrow('function solve(values) { return values.length; }').status,'rewritten');
assert(fragments(source).every(x=>source.includes(x)));console.log(JSON.stringify({passed:7,scope:'Guarded rewrite rejection and exact AST substring extraction; semantic qualification is separate.'}));
