'use strict';
const assert = require('node:assert/strict');
const {review} = require('./source_host_review.cjs');
for (const [source, reason] of [
  ['function solve(){return Date.now()}', 'external_name:Date'],
  ['function solve(){const m=Math;return m.random()}', 'reflection_or_nondeterministic_property:random'],
  ['function solve(){return require("fs")}', 'external_name:require'],
  ['function solve(x,k){return x[k]()}', 'dynamic_member_call'],
  ['function solve(x){return x.constructor("return 1")()}', 'reflection_or_nondeterministic_property:constructor'],
  ['async function solve(x){return await x}', 'unsupported_construct:FunctionDeclaration'],
  ['function solve(k){const m=Math;const fn=m[k];return fn()}', 'dynamic_host_property'],
  ['function solve(k){const fn=({})[k];return fn()}', 'dynamic_callable_alias'],
  ['function solve(){const {random: draw}=Math;return draw()}', 'reflection_or_nondeterministic_property:random'],
]) assert(review(source).unsupported.includes(reason), reason);
const pure = review('function solve(values){const counts=new Map();for(const value of values)counts.set(value,(counts.get(value)||0)+1);return [...counts.values()]}');
assert.deepEqual(pure.unsupported, []);
assert.deepEqual(pure.globals, ['Map']);
assert.deepEqual(review('function helper(x){return x+1} function solve(x){return helper(x)}').unsupported, []);
assert.equal(pure.determinism_proved, false);
assert.equal(pure.browser_admitted, false);
assert.equal(review('throw new Error("never execute");function solve(x){return x}').source_executed, false);
console.log('Static host observation regressions passed');
