'use strict';

// 712. Minimum ASCII Delete Sum for Two Strings.

function solve(s1, s2) {
  const dp = [0];
  for (let j = 0; j < s2.length; j += 1) dp.push(dp[dp.length - 1] + s2.charCodeAt(j));
  for (let i = 0; i < s1.length; i += 1) {
    let diagonal = dp[0]; dp[0] += s1.charCodeAt(i);
    for (let j = 1; j <= s2.length; j += 1) {
      const previous = dp[j];
      dp[j] = s1[i] === s2[j - 1] ? diagonal : Math.min(dp[j] + s1.charCodeAt(i), dp[j - 1] + s2.charCodeAt(j - 1));
      diagonal = previous;
    }
  }
  return dp[dp.length - 1];
}

const minimumDeleteSum = solve;
class Solution {
  minimumDeleteSum(s1, s2) { return solve(s1, s2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumDeleteSum };
