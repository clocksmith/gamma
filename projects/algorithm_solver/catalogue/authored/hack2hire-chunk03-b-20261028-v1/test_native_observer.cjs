'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const M1 = 'hack2hire:691e23ea08ad7861624b569b';
class MusicPlayer {
  constructor() { this.titles = []; this.users = new Map(); }
  addSong(t) { this.titles.push(t); return this.titles.length; }
  playSong(s, u) { if (!this.users.has(s)) this.users.set(s, new Set()); this.users.get(s).add(u); }
  getAnalytics() { return this.titles.map((t, i) => [t, (this.users.get(i + 1) || new Set()).size]); }
}
const args = [['MusicPlayer', 'addSong', 'playSong', 'getAnalytics'], [[], ['A'], [1, 4], []]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({MusicPlayer}, M1, {args}, transport);
  assert.deepStrictEqual(r.result, [null, 1, null, [['A', 1]]]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'number', 'undefined', 'object']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
class Leaky extends MusicPlayer { playSong() { return 0; } }
assert.deepStrictEqual(h.observe({MusicPlayer: Leaky}, M1, {args}, transport).native_method_return_types[2], 'number');
assert.throws(() => h.observe({solve: () => []}, M1, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
assert.throws(() => h.shape(M1, [['MusicPlayer', 'removeSong'], [[], [1]]]));
console.log('5 source-free JS observer controls passed');
