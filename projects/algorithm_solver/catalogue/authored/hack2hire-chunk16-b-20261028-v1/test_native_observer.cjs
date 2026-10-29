'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const T = 'hack2hire:68aceb961bf7d2097f647f62';
class ProductPrice {
  constructor() { this.prices = new Map(); }
  update(timestamp, price) { this.prices.set(timestamp, price); }
  current() { return this.prices.size ? this.prices.get(Math.max(...this.prices.keys())) : -1; }
  maximum() { return this.prices.size ? Math.max(...this.prices.values()) : -1; }
  minimum() { return this.prices.size ? Math.min(...this.prices.values()) : -1; }
}
const args = [['ProductPrice', 'update', 'current'], [[], [3, 7], []]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({ProductPrice}, T, {args}, transport);
  assert.deepStrictEqual(r.result, [null, null, 7]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'undefined', 'number']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({ProductPrice}, T, {args: [['ProductPrice', 'update', 'update', 'maximum', 'minimum'], [[], [1, 4], [2, 9], [], []]]}, transport);
assert.deepStrictEqual(s.result, [null, null, null, 9, 4]);
assert.throws(() => h.observe({solve: () => []}, T, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
