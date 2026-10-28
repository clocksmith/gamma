'use strict';

// 918. Maximum Sum Circular Subarray (Medium).
// Specification: https://leetcode.com/problems/maximum-sum-circular-subarray/description/
function solve(nums) {
  let total = 0; let maxEnding = nums[0]; let maxSoFar = nums[0]; let minEnding = nums[0]; let minSoFar = nums[0];
  for (const v of nums) {
    total += v;
  }
  for (let i = 1; i < nums.length; i++) {
    maxEnding = Math.max(nums[i], maxEnding + nums[i]);
    maxSoFar = Math.max(maxSoFar, maxEnding);
    minEnding = Math.min(nums[i], minEnding + nums[i]);
    minSoFar = Math.min(minSoFar, minEnding);
  }
  if (maxSoFar < 0) return maxSoFar;
  return Math.max(maxSoFar, total - minSoFar);
}
const maxSubarraySumCircular = solve;
class Solution { maxSubarraySumCircular(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSubarraySumCircular };
