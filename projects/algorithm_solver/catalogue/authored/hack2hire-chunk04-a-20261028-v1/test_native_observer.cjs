'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const ITER = 'hack2hire:677bf4df5cbaff553b53b068', SNAP1 = 'hack2hire:69b191c3a4e93c007df4004d';
class SubarrayFirstIterator { constructor(a, b) { this.items = b.concat(a); } hasNext() { return this.items.length > 0; } next() { return this.items.shift(); } }
const args = [['SubarrayFirstIterator', 'next', 'hasNext'], [[[], [7]], [], []]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({SubarrayFirstIterator}, ITER, {args}, transport);
  assert.deepStrictEqual(r.result, [null, 7, false]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'number', 'boolean']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
class SocialNetwork { constructor() { this.e = new Set(); this.s = []; } follow(f, e) { this.e.add(f + ',' + e); } unfollow(f, e) { this.e.delete(f + ',' + e); }
  snapshot() { this.s.push(new Set(this.e)); return this.s.length - 1; } isFollowing(f, e, s) { return this.s[s].has(f + ',' + e); } }
const s = h.observe({SocialNetwork}, SNAP1, {args: [['SocialNetwork', 'follow', 'snapshot', 'isFollowing'], [[], [1, 2], [], [1, 2, 0]]]}, transport);
assert.deepStrictEqual(s.result, [null, null, 0, true]);
assert.deepStrictEqual(s.native_method_return_types, ['constructed', 'undefined', 'number', 'boolean']);
assert.throws(() => h.observe({solve: () => []}, ITER, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
