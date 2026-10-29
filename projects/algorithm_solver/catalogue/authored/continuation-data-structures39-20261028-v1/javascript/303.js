"use strict";

class NumArray {
  constructor(nums) {
    const prefix = new Array(nums.length + 1);
    prefix[0] = 0;
    let running = 0;
    for (let i = 0; i < nums.length; i++) {
      running += nums[i];
      prefix[i + 1] = running;
    }
    this.prefix = prefix;
  }
  sumRange(left, right) {
    return this.prefix[right + 1] - this.prefix[left];
  }
}

function solve(operation_names, argument_lists) {
  const instance = new NumArray(argument_lists[0][0]);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i];
    const args = argument_lists[i];
    if (op === "sumRange") {
      out.push(instance.sumRange(args[0], args[1]));
    } else {
      throw new Error("unknown operation");
    }
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.NumArray = NumArray;
