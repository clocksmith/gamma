'use strict';

// 322. Coin Change (Medium).
// Specification: https://leetcode.com/problems/coin-change/description/
function solve(coins, amount) {
  const dp = new Array(amount + 1).fill(Infinity);
  dp[0] = 0;
  for (let value = 1; value <= amount; value++) {
    for (const coin of coins) { if (coin <= value) dp[value] = Math.min(dp[value], dp[value - coin] + 1); }
  }
  return dp[amount] === Infinity ? -1 : dp[amount];
}
const coinChange = solve;
class Solution { coinChange(coins, amount) { return solve(coins, amount); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, coinChange };
