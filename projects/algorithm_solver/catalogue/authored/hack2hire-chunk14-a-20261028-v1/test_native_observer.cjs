'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const T = 'hack2hire:681d10c6cc14e2629f006012';
class PinManager {
  constructor() { this.pins = []; }
  addPin(pinId, score, pinType) { this.pins.push([pinId, score, pinType]); }
  getTopK(pinType, k) { return this.pins.filter((p) => p[2] === pinType).sort((a, b) => b[1] - a[1] || a[0] - b[0]).slice(0, k).map((p) => p[0]); }
}
const args = [['PinManager', 'addPin', 'getTopK'], [[], [4, 2, 'a'], ['a', 5]]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({PinManager}, T, {args}, transport);
  assert.deepStrictEqual(r.result, [null, null, [4]]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'undefined', 'object']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({PinManager}, T, {args: [['PinManager', 'addPin', 'addPin', 'addPin', 'getTopK'], [[], [9, 1, 'a'], [3, 1, 'a'], [5, 7, 'b'], ['a', 9]]]}, transport);
assert.deepStrictEqual(s.result, [null, null, null, null, [3, 9]]);
assert.throws(() => h.observe({solve: () => []}, T, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
