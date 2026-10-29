'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const T = 'hack2hire:68e2d042dab409e303d92952';
class MovieFriends {
  constructor(k) { this.last = new Map(); }
  watch(customerId, movieId) { this.last.set(customerId, movieId); }
  getFriends(customerId) { const me = this.last.get(customerId); return [...this.last].filter(([c, m]) => c !== customerId && m === me).map(([c]) => c).sort(); }
}
const args = [['MovieFriends', 'watch', 'getFriends'], [[1], ['a', 'h'], ['a']]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({MovieFriends}, T, {args}, transport);
  assert.deepStrictEqual(r.result, [null, null, []]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'undefined', 'object']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({MovieFriends}, T, {args: [['MovieFriends', 'watch', 'watch', 'getFriends'], [[1], ['b', 'm'], ['c', 'm'], ['b']]]}, transport);
assert.deepStrictEqual(s.result, [null, null, null, ['c']]);
assert.throws(() => h.observe({solve: () => []}, T, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
