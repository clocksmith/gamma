'use strict';

// 3375. Minimum Operations to Make Array Values Equal to K (Easy).
// Specification: https://leetcode.com/problems/minimum-operations-to-make-array-values-equal-to-k/description/
// O(n) expected time and O(n) space; count distinct levels strictly above k.
function solve(nums, k) {
  const levels = new Set();
  for (const value of nums) {
    if (value < k) return -1;
    if (value > k) levels.add(value);
  }
  return levels.size;
}

const minOperations = solve;
class Solution {
  minOperations(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
