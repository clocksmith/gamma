'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const T = 'hack2hire:679da470996c3c60bd38b5ba';
class AlienBaseAttack {
  constructor(n) { this.n = n; this.hits = []; }
  attack(x) { this.hits.push(x); }
  isDestroyed() { for (let i = 0; i < this.n; i++) if (!this.hits.includes(i)) return false; return true; }
}
const args = [['AlienBaseAttack', 'attack', 'isDestroyed'], [[1], [0], []]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({AlienBaseAttack}, T, {args}, transport);
  assert.deepStrictEqual(r.result, [null, null, true]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'undefined', 'boolean']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({AlienBaseAttack}, T, {args: [['AlienBaseAttack', 'attack', 'isDestroyed', 'attack', 'isDestroyed'], [[2], [1], [], [0], []]]}, transport);
assert.deepStrictEqual(s.result, [null, null, false, null, true]);
assert.throws(() => h.observe({solve: () => []}, T, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
