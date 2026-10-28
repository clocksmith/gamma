'use strict';

// 1035. Uncrossed Lines (Medium).
// Specification: https://leetcode.com/problems/uncrossed-lines/description/
function solve(nums1, nums2) {
  const dp = new Array(nums2.length + 1).fill(0);
  for (const a of nums1) {
    let previous = 0;
    for (let j = 0; j < nums2.length; j++) {
      const saved = dp[j + 1];
      if (a === nums2[j]) dp[j + 1] = previous + 1;
      else dp[j + 1] = Math.max(dp[j + 1], dp[j]);
      previous = saved;
    }
  }
  return dp[nums2.length];
}
const maxUncrossedLines = solve;
class Solution { maxUncrossedLines(nums1, nums2) { return solve(nums1, nums2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxUncrossedLines };
