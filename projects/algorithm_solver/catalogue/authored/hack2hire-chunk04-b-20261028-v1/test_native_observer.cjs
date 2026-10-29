'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const C1 = 'hack2hire:6a579fe2665efda9311f9375', C2 = 'hack2hire:6a579fe4665efda9311f9376';
class ChatEventAggregator {
  constructor(m) { this.m = m; this.seen = []; }
  recordEvent(t, u) { this.seen.push([t, u]); }
  getUserCount(t, u) { return this.seen.filter(([x, y]) => y === u && x > t - this.m).length; }
  getChatCount() { return this.seen.length; }
}
const args = [['ChatEventAggregator', 'recordEvent', 'getUserCount'], [[5], [1, 'al', 'c'], [3, 'al']]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({ChatEventAggregator}, C1, {args}, transport);
  assert.deepStrictEqual(r.result, [null, null, 1]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'undefined', 'number']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({ChatEventAggregator}, C2, {args: [['ChatEventAggregator', 'recordEvent', 'getChatCount'], [[3], [0, 'al', 'c1'], [0, 'c1']]]}, transport);
assert.deepStrictEqual(s.result, [null, null, 1]);
assert.throws(() => h.observe({solve: () => []}, C1, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
