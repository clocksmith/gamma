'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const T = 'hack2hire:68099e1fcbb5948f87732b56';
class KVStore {
  constructor() { this.data = new Map(); }
  set(key, value) { this.data.set(key, value); }
  get(key) { return this.data.has(key) ? this.data.get(key) : -1; }
  update(key, value) { this.data.set(key, value); }
  deleteKey(key) { this.data.delete(key); }
  prefixSearch(prefix) { return [...this.data.keys()].filter((k) => k.startsWith(prefix)).sort().map((k) => this.data.get(k)); }
}
const args = [['KVStore', 'set', 'get'], [[], ['a', 5], ['a']]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({KVStore}, T, {args}, transport);
  assert.deepStrictEqual(r.result, [null, null, 5]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'undefined', 'number']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({KVStore}, T, {args: [['KVStore', 'prefixSearch'], [[], ['']]]}, transport);
assert.deepStrictEqual(s.result, [null, []]);
assert.throws(() => h.observe({solve: () => []}, T, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
