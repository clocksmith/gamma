'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const T = 'hack2hire:677df76b052a260e0165706c';
class InfiniteQueue {
  constructor() { this.items = []; }
  add(value) { this.items.push(value); }
  poll() { return this.items.length ? this.items.shift() : -1; }
  getRandom(r) { return this.items.length ? this.items[r % this.items.length] : -1; }
}
const args = [['InfiniteQueue', 'add', 'poll'], [[], [7], []]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({InfiniteQueue}, T, {args}, transport);
  assert.deepStrictEqual(r.result, [null, null, 7]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'undefined', 'number']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({InfiniteQueue}, T, {args: [['InfiniteQueue', 'add', 'add', 'getRandom', 'poll'], [[], [1], [2], [3], []]]}, transport);
assert.deepStrictEqual(s.result, [null, null, null, 2, 1]);
assert.throws(() => h.observe({solve: () => []}, T, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
