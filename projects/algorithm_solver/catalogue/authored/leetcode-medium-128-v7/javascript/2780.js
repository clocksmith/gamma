'use strict';

// 2780. Minimum Index of a Valid Split: find the dominant candidate and check both sides of each split.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums) {
  let candidate = 0;
  let balance = 0;
  for (const value of nums) {
    if (balance === 0) candidate = value;
    balance += value === candidate ? 1 : -1;
  }
  let total = 0;
  for (const value of nums) if (value === candidate) total += 1;
  let prefix = 0;
  for (let index = 0; index + 1 < nums.length; index += 1) {
    if (nums[index] === candidate) prefix += 1;
    if (2 * prefix > index + 1 && 2 * (total - prefix) > nums.length - index - 1) return index;
  }
  return -1;
}

const minimumIndex = solve;
class Solution {
  minimumIndex(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumIndex };
