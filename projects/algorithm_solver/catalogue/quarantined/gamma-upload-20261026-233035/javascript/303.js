'use strict';
// 303. Range Sum Query - Immutable.
class NumArray {
  constructor(nums) {
    this.prefix = [0];
    for (const value of nums) this.prefix.push(this.prefix[this.prefix.length - 1] + value);
  }
  sumRange(left, right) { return this.prefix[right + 1] - this.prefix[left]; }
}
function solve(nums, queries) {
  const array = new NumArray(nums);
  return queries.map(query => array.sumRange(...query));
}
if (typeof module !== 'undefined') module.exports = { solve, NumArray };
