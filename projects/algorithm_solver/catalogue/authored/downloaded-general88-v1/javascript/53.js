'use strict';

// 53. Maximum Subarray (Medium).
// Specification: https://leetcode.com/problems/maximum-subarray/description/
function solve(nums) {
  let best = nums[0]; let current = nums[0];
  for (let i = 1; i < nums.length; i++) { current = Math.max(nums[i], current + nums[i]); best = Math.max(best, current); }
  return best;
}
const maxSubArray = solve;
class Solution { maxSubArray(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSubArray };
