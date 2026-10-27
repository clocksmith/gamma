// Original candidate implementation. Contract: https://leetcode.com/problems/number-of-ways-to-earn-points/
"use strict";

function solve(target, types) {
  const modulus = 1000000007;
  let dp = Array(target + 1).fill(0);
  dp[0] = 1;
  for (const [count, marks] of types) {
    const next = Array(target + 1).fill(0);
    for (let score = 0; score <= target; score++) {
      for (let take = 0; take <= count && take * marks <= score; take++) {
        next[score] = (next[score] + dp[score - take * marks]) % modulus;
      }
    }
    dp = next;
  }
  return dp[target];
}

module.exports = solve;
