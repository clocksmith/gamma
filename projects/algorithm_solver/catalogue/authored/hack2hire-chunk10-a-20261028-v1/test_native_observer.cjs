'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const T = 'hack2hire:6920d01494b324049c3251bd';
class KeyValueStore {
  constructor() { this.data = new Map(); }
  set(key, value) { this.data.set(key, value); }
  get(key) { return this.data.get(key) || ''; }
  unset(key) { this.data.delete(key); }
}
const args = [['KeyValueStore', 'set', 'get'], [[], ['a', 'h'], ['a']]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({KeyValueStore}, T, {args}, transport);
  assert.deepStrictEqual(r.result, [null, null, 'h']);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'undefined', 'string']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({KeyValueStore}, T, {args: [['KeyValueStore', 'get'], [[], ['b']]]}, transport);
assert.deepStrictEqual(s.result, [null, '']);
assert.throws(() => h.observe({solve: () => []}, T, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
