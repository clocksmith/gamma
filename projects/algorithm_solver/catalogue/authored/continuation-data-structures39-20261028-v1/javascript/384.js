"use strict";

class Solution {
  constructor(nums) {
    this.orig = nums.slice();
    this._state = 0x9e3779b9 >>> 0;
  }
  _randrange(n) {
    this._state = (Math.imul(this._state, 1664525) + 1013904223) >>> 0;
    return this._state % n;
  }
  reset() {
    return this.orig.slice();
  }
  shuffle() {
    const arr = this.orig.slice();
    for (let i = arr.length - 1; i > 0; i--) {
      const j = this._randrange(i + 1);
      const t = arr[i];
      arr[i] = arr[j];
      arr[j] = t;
    }
    return arr;
  }
}

function solve(operation_names, argument_lists) {
  const instance = new Solution(argument_lists[0][0]);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i];
    if (op === "reset") out.push(instance.reset());
    else if (op === "shuffle") out.push(instance.shuffle());
    else throw new Error("unknown operation");
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.Solution = Solution;
