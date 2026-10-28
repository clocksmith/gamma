'use strict';

// 97. Interleaving String (Medium).
// Specification: https://leetcode.com/problems/interleaving-string/description/
function solve(s1, s2, s3) {
  if (s1.length + s2.length !== s3.length) return false;
  const dp = new Array(s2.length + 1).fill(false);
  dp[0] = true;
  for (let j = 1; j <= s2.length; j++) dp[j] = dp[j - 1] && s2[j - 1] === s3[j - 1];
  for (let i = 1; i <= s1.length; i++) {
    dp[0] = dp[0] && s1[i - 1] === s3[i - 1];
    for (let j = 1; j <= s2.length; j++) {
      dp[j] = (dp[j] && s1[i - 1] === s3[i + j - 1]) || (dp[j - 1] && s2[j - 1] === s3[i + j - 1]);
    }
  }
  return dp[s2.length];
}
const isInterleave = solve;
class Solution { isInterleave(s1, s2, s3) { return solve(s1, s2, s3); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isInterleave };
