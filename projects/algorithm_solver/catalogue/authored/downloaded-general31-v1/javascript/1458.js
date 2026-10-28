'use strict';

// 1458. Max Dot Product of Two Subsequences (Medium).
// Specification: https://leetcode.com/problems/max-dot-product-of-two-subsequences/description/
function solve(nums1, nums2) {
  const NEG = -1000000000000000;
  const dp = Array.from({ length: nums1.length + 1 }, () => new Array(nums2.length + 1).fill(NEG));
  for (let i = 1; i <= nums1.length; i++) {
    for (let j = 1; j <= nums2.length; j++) {
      const product = nums1[i - 1] * nums2[j - 1];
      let best = Math.max(dp[i - 1][j], dp[i][j - 1], product);
      if (dp[i - 1][j - 1] !== NEG) best = Math.max(best, dp[i - 1][j - 1] + product);
      dp[i][j] = best;
    }
  }
  return dp[nums1.length][nums2.length];
}
const maxDotProduct = solve;
class Solution { maxDotProduct(nums1, nums2) { return solve(nums1, nums2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxDotProduct };
