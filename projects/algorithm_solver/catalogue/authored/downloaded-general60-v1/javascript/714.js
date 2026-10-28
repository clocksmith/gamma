'use strict';

// 714. Best Time to Buy and Sell Stock with Transaction Fee (Medium).
// Specification: https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-transaction-fee/description/
function solve(prices, fee) {
  let cash = 0; let hold = -Infinity;
  for (const price of prices) {
    const previousCash = cash;
    cash = Math.max(cash, hold + price - fee);
    hold = Math.max(hold, previousCash - price);
  }
  return cash;
}
const maxProfit = solve;
class Solution { maxProfit(prices, fee) { return solve(prices, fee); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProfit };
