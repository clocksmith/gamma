'use strict';

// 2441. Largest Positive Integer That Exists With Its Negative (Easy).
// Specification: https://leetcode.com/problems/largest-positive-integer-that-exists-with-its-negative/description/
// O(n) expected time, O(n) space; preserve nums.
function solve(nums) {
  const values = new Set(nums);
  let result = -1;
  for (const value of nums) {
    if (value > 0 && values.has(-value)) result = Math.max(result, value);
  }
  return result;
}

const findMaxK = solve;
class Solution {
  findMaxK(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaxK };
