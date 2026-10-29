'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const T = 'hack2hire:6a2db7bc5117d1b543565e24';
class FunctionCallCache {
  constructor(capacity) { this.seen = []; }
  call(functionName, args, kwargs) {
    const key = JSON.stringify([functionName, args, kwargs]);
    if (this.seen.includes(key)) return true;
    this.seen.push(key); return false;
  }
}
const args = [['FunctionCallCache', 'call', 'call'], [[1], ['f', [1], {}], ['f', [1], {}]]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({FunctionCallCache}, T, {args}, transport);
  assert.deepStrictEqual(r.result, [null, false, true]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'boolean', 'boolean']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({FunctionCallCache}, T, {args: [['FunctionCallCache', 'call', 'call', 'call'], [[3], ['f', [], {}], ['g', [], {}], ['f', [], {}]]]}, transport);
assert.deepStrictEqual(s.result, [null, false, false, true]);
assert.throws(() => h.observe({solve: () => []}, T, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
