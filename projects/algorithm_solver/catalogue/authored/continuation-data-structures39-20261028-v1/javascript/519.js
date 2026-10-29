"use strict";

class Solution {
  constructor(m, n) {
    this.m = Number(m);
    this.n = Number(n);
    this.total = this.m * this.n;
    this.swapped = new Map();
    this._state = 0x9e3779b9 >>> 0;
  }
  _randrange(k) {
    this._state = (Math.imul(this._state, 1664525) + 1013904223) >>> 0;
    return this._state % k;
  }
  flip() {
    const r = this._randrange(this.total);
    this.total -= 1;
    const idx = this.swapped.has(r) ? this.swapped.get(r) : r;
    const tail = this.swapped.has(this.total) ? this.swapped.get(this.total) : this.total;
    this.swapped.set(r, tail);
    return [Math.floor(idx / this.n), idx % this.n];
  }
  reset() {
    this.total = this.m * this.n;
    this.swapped.clear();
  }
}

function solve(operation_names, argument_lists) {
  const [m, n] = argument_lists[0];
  const instance = new Solution(m, n);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i];
    if (op === "flip") out.push(instance.flip());
    else if (op === "reset") { instance.reset(); out.push(null); }
    else throw new Error("unknown operation");
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.Solution = Solution;
