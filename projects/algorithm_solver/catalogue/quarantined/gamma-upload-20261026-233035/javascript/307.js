'use strict';
// 307. Range Sum Query - Mutable.
class NumArray {
  constructor(nums) {
    this.values = nums.slice(); this.tree = Array(nums.length + 1).fill(0);
    nums.forEach((value, index) => this.add(index + 1, value));
  }
  add(index, difference) { while (index < this.tree.length) { this.tree[index] += difference; index += index & -index; } }
  update(index, val) { const difference = val - this.values[index]; this.values[index] = val; this.add(index + 1, difference); }
  prefix(index) { let total = 0; while (index) { total += this.tree[index]; index -= index & -index; } return total; }
  sumRange(left, right) { return this.prefix(right + 1) - this.prefix(left); }
}
function solve(nums, operations, args) {
  const structure = new NumArray(nums);
  return operations.map((operation, index) => structure[operation](...args[index]));
}
if (typeof module !== 'undefined') module.exports = { solve, NumArray };
