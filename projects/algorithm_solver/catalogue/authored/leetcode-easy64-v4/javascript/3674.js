'use strict';

// 3674. Minimum Operations to Equalize Array (Easy).
// Specification: https://leetcode.com/problems/minimum-operations-to-equalize-array/description/
// O(n) time, O(1) space; one whole-array AND operation suffices if unequal.
function solve(nums) {
  for (const value of nums) {
    if (value !== nums[0]) return 1;
  }
  return 0;
}

const minOperations = solve;
class Solution {
  minOperations(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
