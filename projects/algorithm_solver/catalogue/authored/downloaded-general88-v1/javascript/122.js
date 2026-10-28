'use strict';

// 122. Best Time to Buy and Sell Stock II (Medium).
// Specification: https://leetcode.com/problems/best-time-to-buy-and-sell-stock-ii/description/
function solve(prices) {
  let profit = 0;
  for (let i = 1; i < prices.length; i++) { if (prices[i] > prices[i - 1]) profit += prices[i] - prices[i - 1]; }
  return profit;
}
const maxProfit = solve;
class Solution { maxProfit(prices) { return solve(prices); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProfit };
