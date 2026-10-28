'use strict';

// 3290. Maximum Multiplication Score (Medium).
// Specification: https://leetcode.com/problems/maximum-multiplication-score/description/
function solve(a, b) {
  const NEG = -Infinity;
  let dp = [0, NEG, NEG, NEG, NEG];
  for (const x of b) {
    for (let t = 4; t >= 1; t--) {
      if (dp[t - 1] !== NEG) dp[t] = Math.max(dp[t], dp[t - 1] + a[t - 1] * x);
    }
  }
  return dp[4];
}
const maxScore = solve;
class Solution { maxScore(a, b) { return solve(a, b); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxScore };
