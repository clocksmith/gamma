"use strict";

class NumArray {
  constructor(nums) {
    const n = nums.length;
    this.n = n;
    this.vals = nums.slice();
    const tree = new Array(n + 1).fill(0);
    for (let i = 0; i < n; i++) tree[i + 1] = nums[i];
    for (let i = 1; i <= n; i++) {
      const j = i + (i & -i);
      if (j <= n) tree[j] += tree[i];
    }
    this.tree = tree;
  }
  update(index, val) {
    const delta = val - this.vals[index];
    this.vals[index] = val;
    for (let i = index + 1; i <= this.n; i += i & -i) {
      this.tree[i] += delta;
    }
  }
  _prefix(i) {
    let s = 0;
    for (; i > 0; i -= i & -i) s += this.tree[i];
    return s;
  }
  sumRange(left, right) {
    return this._prefix(right + 1) - this._prefix(left);
  }
}

function solve(operation_names, argument_lists) {
  const instance = new NumArray(argument_lists[0][0]);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i];
    const args = argument_lists[i];
    if (op === "update") {
      instance.update(args[0], args[1]);
      out.push(null);
    } else if (op === "sumRange") {
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
