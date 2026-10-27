'use strict';
// 188. Best Time to Buy and Sell Stock IV.
function solve(k, prices) {
  if (prices.length === 0 || k === 0) return 0;
  if (k >= Math.floor(prices.length / 2)) {
    let total = 0;
    for (let index = 1; index < prices.length; index += 1) total += Math.max(0, prices[index] - prices[index - 1]);
    return total;
  }
  const buy = Array(k + 1).fill(-Infinity);
  const sell = Array(k + 1).fill(0);
  for (const price of prices) for (let transaction = 1; transaction <= k; transaction += 1) {
    buy[transaction] = Math.max(buy[transaction], sell[transaction - 1] - price);
    sell[transaction] = Math.max(sell[transaction], buy[transaction] + price);
  }
  return sell[k];
}
const maxProfit = solve;
class Solution { maxProfit(k, prices) { return solve(k, prices); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProfit };
