'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const T = 'hack2hire:677595ec0d31dc201f712037';
class PointMatrix {
  constructor() { this.points = []; }
  addPoint(row, col) { this.points.push(row + ',' + col); }
  isConnected(p, q) { return this.points.includes(p.join()) && this.points.includes(q.join()); }
  getMinSteps(s, e) { return this.isConnected(s, e) ? (s.join() === e.join() ? 0 : 1) : -1; }
}
const args = [['PointMatrix', 'addPoint', 'isConnected', 'getMinSteps'], [[], [1, 2], [[1, 2], [1, 2]], [[1, 2], [3, 3]]]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({PointMatrix}, T, {args}, transport);
  assert.deepStrictEqual(r.result, [null, null, true, -1]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'undefined', 'boolean', 'number']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({PointMatrix}, T, {args: [['PointMatrix', 'getMinSteps'], [[], [[0, 0], [0, 0]]]]}, transport);
assert.deepStrictEqual(s.result, [null, -1]);
assert.throws(() => h.observe({solve: () => []}, T, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
