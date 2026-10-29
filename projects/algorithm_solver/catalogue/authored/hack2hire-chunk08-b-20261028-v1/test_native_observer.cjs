'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const S = 'hack2hire:68c48c55e558bc07a7541e31', T = 'hack2hire:684cd590cab8e9bb7ea93b11';
class SnakeGame {   // toy: only walls, no body
  constructor(rows, cols) { this.rows = rows; this.cols = cols; this.c = 0; }
  move(d) { this.c += d === 'R' ? 1 : d === 'L' ? -1 : 0; return this.c >= 0 && this.c < this.cols; }
}
class TicTacToe {   // toy: wins on the k-th mark of a player anywhere
  constructor(n, m, k) { this.k = k; this.count = [0, 0, 0]; }
  move(r, c, p) { return ++this.count[p] >= this.k ? p : 0; }
}
const args = [['SnakeGame', 'move', 'move'], [[1, 2], ['R'], ['R']]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({SnakeGame}, S, {args}, transport);
  assert.deepStrictEqual(r.result, [null, true, false]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'boolean', 'boolean']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const t = h.observe({TicTacToe}, T, {args: [['TicTacToe', 'move', 'move'], [[3, 3, 2], [0, 0, 1], [1, 1, 1]]]}, transport);
assert.deepStrictEqual(t.result, [null, 0, 1]);
assert.throws(() => h.observe({solve: () => []}, S, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
