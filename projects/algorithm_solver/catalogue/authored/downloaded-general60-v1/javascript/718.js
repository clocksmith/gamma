'use strict';

// 718. Maximum Length of Repeated Subarray (Medium).
// Specification: https://leetcode.com/problems/maximum-length-of-repeated-subarray/description/
function solve(nums1, nums2) {
  const m = nums1.length; const n = nums2.length;
  const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  let best = 0;
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (nums1[i - 1] === nums2[j - 1]) { dp[i][j] = dp[i - 1][j - 1] + 1; best = Math.max(best, dp[i][j]); }
    }
  }
  return best;
}
const findLength = solve;
class Solution { findLength(nums1, nums2) { return solve(nums1, nums2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLength };
