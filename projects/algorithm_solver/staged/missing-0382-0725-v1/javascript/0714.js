'use strict';

// 714. Best Time to Buy and Sell Stock with Transaction Fee.

function solve(prices, fee) {
  if (prices.length === 0) return 0;
  let cash = 0, holding = -prices[0];
  for (let i = 1; i < prices.length; i += 1) [cash, holding] = [Math.max(cash, holding + prices[i] - fee), Math.max(holding, cash - prices[i])];
  return cash;
}

const maxProfit = solve;
class Solution {
  maxProfit(prices, fee) { return solve(prices, fee); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProfit };
