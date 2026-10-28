'use strict';

// 2229. Check if an Array Is Consecutive (Easy).
// Specification: https://leetcode.com/problems/check-if-an-array-is-consecutive/description/
function solve(nums) {
  if (nums.length === 0) return false;
  const seen = new Set(nums);
  if (seen.size !== nums.length) return false;
  return Math.max(...nums) - Math.min(...nums) === nums.length - 1;
}
const isConsecutive = solve;
class Solution { isConsecutive(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isConsecutive };
