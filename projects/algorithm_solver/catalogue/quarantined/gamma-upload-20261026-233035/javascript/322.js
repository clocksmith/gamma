'use strict';
// 322. Coin Change.
function solve(coins, amount) {
  const dp = Array(amount + 1).fill(amount + 1); dp[0] = 0;
  for (let value = 1; value <= amount; value += 1) {
    for (const coin of coins) if (coin <= value) dp[value] = Math.min(dp[value], dp[value - coin] + 1);
  }
  return dp[amount] > amount ? -1 : dp[amount];
}
const coinChange = solve;
class Solution { coinChange(coins, amount) { return solve(coins, amount); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, coinChange };
