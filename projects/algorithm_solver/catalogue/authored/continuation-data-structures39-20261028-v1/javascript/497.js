"use strict";

class Solution {
  constructor(rects) {
    this.rects = rects.map((r) => [r[0], r[1], r[2], r[3]]);
    const prefix = [];
    let total = 0;
    for (let i = 0; i < this.rects.length; i++) {
      const [a, b, x, y] = this.rects[i];
      total += (x - a + 1) * (y - b + 1);
      prefix.push(total);
    }
    this.prefix = prefix;
    this.total = total;
    this._state = 0x9e3779b9 >>> 0;
  }
  _randrange(n) {
    this._state = (Math.imul(this._state, 1664525) + 1013904223) >>> 0;
    return this._state % n;
  }
  pick() {
    const t = this._randrange(this.total);
    let low = 0, high = this.prefix.length - 1;
    while (low < high) {
      const mid = (low + high) >> 1;
      if (this.prefix[mid] <= t) low = mid + 1;
      else high = mid;
    }
    const idx = low;
    const base = idx === 0 ? 0 : this.prefix[idx - 1];
    const offset = t - base;
    const [a, b, x] = this.rects[idx];
    const w = x - a + 1;
    return [a + (offset % w), b + Math.floor(offset / w)];
  }
}

function solve(operation_names, argument_lists) {
  const instance = new Solution(argument_lists[0][0]);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i];
    if (op === "pick") out.push(instance.pick());
    else throw new Error("unknown operation");
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.Solution = Solution;
