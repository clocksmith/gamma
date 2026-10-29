'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const T = 'hack2hire:678879df402dc47b67a14946';
class SearchHistory {
  constructor(capacity) { this.capacity = capacity; this.items = []; }
  add(term) { this.items = [term, ...this.items.filter((t) => t !== term)].slice(0, this.capacity); }
  getTopK(k) { return this.items.slice(0, k); }
}
const args = [['SearchHistory', 'add', 'getTopK'], [[2], ['a'], [5]]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({SearchHistory}, T, {args}, transport);
  assert.deepStrictEqual(r.result, [null, null, ['a']]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'undefined', 'object']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({SearchHistory}, T, {args: [['SearchHistory', 'add', 'add', 'add', 'getTopK'], [[2], ['a'], ['b'], ['a'], [9]]]}, transport);
assert.deepStrictEqual(s.result, [null, null, null, null, ['a', 'b']]);
assert.throws(() => h.observe({solve: () => []}, T, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
