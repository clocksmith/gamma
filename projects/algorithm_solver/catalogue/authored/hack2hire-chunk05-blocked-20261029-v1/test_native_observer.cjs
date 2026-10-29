'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const T = 'hack2hire:6a14a84c7b0582b352787d44';
class ALSWrapper {
  constructor() { this.rows = []; }
  record(status, lux, timestamp) { if (status === 1) this.rows.push([timestamp, lux]); }
  getLatestLux() { let best = null; for (const r of this.rows) if (best === null || r[0] >= best[0]) best = r; return best === null ? -1 : best[1]; }
  getAverageLux(s, e) { const v = this.rows.filter((r) => r[0] >= s && r[0] <= e).map((r) => r[1]); return v.length ? Math.floor(v.reduce((a, b) => a + b, 0) / v.length) : -1; }
}
const args = [['ALSWrapper', 'record', 'getLatestLux'], [[], [1, 5, 2], []]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({ALSWrapper}, T, {args}, transport);
  assert.deepStrictEqual(r.result, [null, null, 5]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'undefined', 'number']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({ALSWrapper}, T, {args: [['ALSWrapper', 'record', 'record', 'getAverageLux', 'getLatestLux'], [[], [1, 4, 1], [0, 9, 3], [0, 5], []]]}, transport);
assert.deepStrictEqual(s.result, [null, null, null, 4, 4]);
assert.throws(() => h.observe({solve: () => []}, T, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
