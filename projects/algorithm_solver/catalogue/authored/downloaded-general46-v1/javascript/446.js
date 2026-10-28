'use strict';

// 446. Arithmetic Slices II - Subsequence (Hard).
// Specification: https://leetcode.com/problems/arithmetic-slices-ii-subsequence/description/
function solve(nums) {
  let total = 0;
  const dp = nums.map(() => ({}));
  for (let i = 0; i < nums.length; i++) {
    for (let j = 0; j < i; j++) {
      const diff = nums[i] - nums[j];
      const previous = dp[j][diff] || 0;
      dp[i][diff] = (dp[i][diff] || 0) + previous + 1;
      total += previous;
    }
  }
  return total;
}
const numberOfArithmeticSlices = solve;
class Solution { numberOfArithmeticSlices(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfArithmeticSlices };
