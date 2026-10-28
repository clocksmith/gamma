'use strict';

// 2907. Maximum Profitable Triplets With Increasing Prices I (Medium).
// Specification: https://leetcode.com/problems/maximum-profitable-triplets-with-increasing-prices-i/description/
function solve(prices, profits) {
  const n = prices.length;
  let ans = -1;
  for (let j = 0; j < n; j++) {
    let left = -1; let right = -1;
    for (let i = 0; i < j; i++) if (prices[i] < prices[j]) left = Math.max(left, profits[i]);
    for (let k = j + 1; k < n; k++) if (prices[k] > prices[j]) right = Math.max(right, profits[k]);
    if (left >= 0 && right >= 0) ans = Math.max(ans, left + profits[j] + right);
  }
  return ans;
}
const maxProfit = solve;
class Solution {
  maxProfit(...args) { return solve(...args); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProfit };
