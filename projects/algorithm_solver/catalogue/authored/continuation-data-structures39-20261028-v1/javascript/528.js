"use strict";

class Solution {
  constructor(w) {
    const prefix = [];
    let total = 0;
    for (let i = 0; i < w.length; i++) {
      total += w[i];
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
  pickIndex() {
    const target = this._randrange(this.total) + 1;
    let low = 0, high = this.prefix.length - 1;
    while (low < high) {
      const mid = (low + high) >> 1;
      if (this.prefix[mid] < target) low = mid + 1;
      else high = mid;
    }
    return low;
  }
}

function solve(operation_names, argument_lists) {
  const instance = new Solution(argument_lists[0][0]);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i];
    if (op === "pickIndex") out.push(instance.pickIndex());
    else throw new Error("unknown operation");
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.Solution = Solution;
