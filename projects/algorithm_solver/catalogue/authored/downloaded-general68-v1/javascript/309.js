'use strict';

// 309. Best Time to Buy and Sell Stock with Cooldown (Medium).
// Specification: https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown/description/
function solve(prices) {
  let hold = -Infinity; let sold = 0; let rest = 0;
  for (const price of prices) {
    const previousHold = hold;
    hold = Math.max(hold, rest - price);
    rest = Math.max(rest, sold);
    sold = previousHold + price;
  }
  return Math.max(sold, rest);
}
const maxProfit = solve;
class Solution { maxProfit(prices) { return solve(prices); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProfit };
