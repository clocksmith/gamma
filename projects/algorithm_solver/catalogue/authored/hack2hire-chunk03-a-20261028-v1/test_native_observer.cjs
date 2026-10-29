'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const ILV = 'hack2hire:678d6982fa7ce9616e190fb3';
class InterleaveIterator {
  constructor(arrays) { this.values = arrays.flat(); }
  hasNext() { return this.values.length > 0; }
  next() { return this.values.length ? this.values.shift() : null; }
}
const args = [['InterleaveIterator', 'next', 'hasNext', 'next'], [[[[7]], false], [], [], []]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({InterleaveIterator}, ILV, {args}, transport);
  assert.deepStrictEqual(r.result, [null, 7, false, null]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'number', 'boolean', 'object']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
assert.throws(() => h.observe({solve: () => []}, ILV, {args}, transport));
assert.throws(() => h.shape(ILV, [['InterleaveIterator', 'peek'], [[[], true], []]]));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
