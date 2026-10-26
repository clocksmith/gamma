'use strict';

// 1413. Minimum Value to Get Positive Step by Step Sum (Easy).
// Specification: https://leetcode.com/problems/minimum-value-to-get-positive-step-by-step-sum/description/
// O(n) time, O(1) space; preserve nums.
function solve(nums) {
  let prefix = 0;
  let lowest = 0;
  for (const value of nums) {
    prefix += value;
    lowest = Math.min(lowest, prefix);
  }
  return 1 - lowest;
}

const minStartValue = solve;
class Solution {
  minStartValue(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minStartValue };
