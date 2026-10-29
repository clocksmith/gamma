'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const T = 'hack2hire:69d17a8817b72775cc49bfe0';
class Table {
  constructor(numRows, numColumns) { this.color = ''; this.size = [numRows, numColumns]; }
  selectTable() {}
  selectRow() {}
  selectCell() {}
  setColor(color) { this.color = color; }
  getColor() { return this.color; }
}
const args = [['Table', 'selectTable', 'setColor', 'getColor'], [[2, 3], [], ['red'], [1, 2]]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({Table}, T, {args}, transport);
  assert.deepStrictEqual(r.result, [null, null, null, 'red']);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'undefined', 'undefined', 'string']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({Table}, T, {args: [['Table', 'getColor'], [[1, 1], [0, 0]]]}, transport);
assert.deepStrictEqual(s.result, [null, '']);
assert.throws(() => h.observe({solve: () => []}, T, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
