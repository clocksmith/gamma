'use strict';

// 121. Best Time to Buy and Sell Stock (Easy).
// Specification: https://leetcode.com/problems/best-time-to-buy-and-sell-stock/description/
// O(n) time, O(1) space; retain the cheapest earlier purchase and best profit.
function solve(prices) {
  let cheapest = Infinity;
  let profit = 0;
  for (const price of prices) {
    cheapest = Math.min(cheapest, price);
    profit = Math.max(profit, price - cheapest);
  }
  return profit;
}

const maxProfit = solve;
class Solution {
  maxProfit(prices) { return solve(prices); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProfit };
