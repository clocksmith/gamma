'use strict';

// 410. Split Array Largest Sum (Hard).
// Specification: https://leetcode.com/problems/split-array-largest-sum/description/
function canSplit(nums, k, limit) {
  let parts = 1; let total = 0;
  for (const value of nums) {
    if (total + value > limit) { parts++; total = value; } else total += value;
  }
  return parts <= k;
}
function solve(nums, k) {
  let left = Math.max(...nums); let right = nums.reduce((sum, value) => sum + value, 0);
  while (left < right) {
    const mid = Math.floor((left + right) / 2);
    if (canSplit(nums, k, mid)) right = mid; else left = mid + 1;
  }
  return left;
}
const splitArray = solve;
class Solution { splitArray(nums, k) { return solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, splitArray };
