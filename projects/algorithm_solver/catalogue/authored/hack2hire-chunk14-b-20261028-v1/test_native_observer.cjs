'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const T = 'hack2hire:68d30311d490dee995152f5b';
class WeightedCache {
  constructor(maxTotalWeight) { this.limit = maxTotalWeight; this.items = []; this.clock = 0; }
  put(key, value, weight) {
    this.items = this.items.filter((it) => it[0] !== key).concat([[key, value, weight, ++this.clock]]);
    while (this.items.reduce((s, it) => s + it[2], 0) > this.limit) {
      let v = this.items[0];
      for (const it of this.items) if (it[2] > v[2] || (it[2] === v[2] && it[3] < v[3])) v = it;
      this.items = this.items.filter((it) => it !== v);
    }
  }
  get(key) { const hit = this.items.find((it) => it[0] === key); return hit ? hit[1] : -1; }
}
const args = [['WeightedCache', 'put', 'get'], [[5], ['a', 7, 2], ['a']]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({WeightedCache}, T, {args}, transport);
  assert.deepStrictEqual(r.result, [null, null, 7]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'undefined', 'number']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({WeightedCache}, T, {args: [['WeightedCache', 'put', 'put', 'get', 'get'], [[5], ['a', 1, 3], ['b', 2, 4], ['a'], ['b']]]}, transport);
assert.deepStrictEqual(s.result, [null, null, null, 1, -1]);
assert.throws(() => h.observe({solve: () => []}, T, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
