"use strict";

class Solution {
  constructor(nums) {
    const indices = new Map();
    for (let i = 0; i < nums.length; i++) {
      const v = nums[i];
      let bucket = indices.get(v);
      if (!bucket) {
        bucket = [];
        indices.set(v, bucket);
      }
      bucket.push(i);
    }
    this.indices = indices;
    this._state = 0x9e3779b9 >>> 0;
  }
  _randrange(n) {
    this._state = (Math.imul(this._state, 1664525) + 1013904223) >>> 0;
    return this._state % n;
  }
  pick(target) {
    const bucket = this.indices.get(target);
    return bucket[this._randrange(bucket.length)];
  }
}

function solve(operation_names, argument_lists) {
  const instance = new Solution(argument_lists[0][0]);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i];
    const args = argument_lists[i];
    if (op === "pick") out.push(instance.pick(args[0]));
    else throw new Error("unknown operation");
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.Solution = Solution;
