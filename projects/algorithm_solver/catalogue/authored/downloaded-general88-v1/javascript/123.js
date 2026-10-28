'use strict';

// 123. Best Time to Buy and Sell Stock III (Hard).
// Specification: https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iii/description/
function solve(prices) {
  let buy1 = -Infinity; let sell1 = 0; let buy2 = -Infinity; let sell2 = 0;
  for (const price of prices) {
    buy1 = Math.max(buy1, -price);
    sell1 = Math.max(sell1, buy1 + price);
    buy2 = Math.max(buy2, sell1 - price);
    sell2 = Math.max(sell2, buy2 + price);
  }
  return sell2;
}
const maxProfit = solve;
class Solution { maxProfit(prices) { return solve(prices); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProfit };
