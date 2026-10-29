'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const WQ1 = 'hack2hire:6ab32819e74ebb7457a3f0f5', SHEET1 = 'hack2hire:69f78c6830f41dfd539fc6dc';
class WorkQueue { constructor(ids) { this.ids = ids.slice(); } reserve() { return this.ids.length ? this.ids.shift() : -1; } }
const args = [['WorkQueue', 'reserve', 'reserve'], [[[7], 5, 1], [0], [1]]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({WorkQueue}, WQ1, {args}, transport);
  assert.deepStrictEqual(r.result, [null, 7, -1]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'number', 'number']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
class Spreadsheet { constructor() { this.v = new Map(); } setCell(c, x) { this.v.set(c, Number(x)); } getCell(c) { return this.v.get(c) || 0; } resetCell(c) { this.v.delete(c); } }
const s = h.observe({Spreadsheet}, SHEET1, {args: [['Spreadsheet', 'setCell', 'getCell'], [[], ['A1', '4'], ['A1']]]}, transport);
assert.deepStrictEqual(s.result, [null, null, 4]);
assert.deepStrictEqual(s.native_method_return_types, ['constructed', 'undefined', 'number']);
assert.throws(() => h.observe({solve: () => []}, WQ1, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
