'use strict';

// 518. Coin Change II. Count unordered coin combinations; exact internal counts and problem-bounded numeric return.

function solve(amount, coins) {
  const dp = Array(amount + 1).fill(0n);
  dp[0] = 1n;
  for (const coin of coins) for (let sum = coin; sum <= amount; sum += 1) dp[sum] += dp[sum - coin];
  return Number(dp[amount]);
}

const change = solve;
class Solution {
  change(amount, coins) { return solve(amount, coins); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, change };
