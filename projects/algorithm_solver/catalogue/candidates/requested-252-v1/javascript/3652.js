'use strict';

// 3652. Best Time to Buy and Sell Stock using Strategy.
// Specification: https://leetcode.com/problems/best-time-to-buy-and-sell-stock-using-strategy/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(n) time and space; k is even, and changing a segment is optional.
// Inputs are not modified.

function solve(prices, strategy, k) {
  const original = [0], priceSum = [0];
  for (let index = 0; index < prices.length; index++) {
    original.push(original[index] + prices[index] * strategy[index]);
    priceSum.push(priceSum[index] + prices[index]);
  }
  let bestGain = 0;
  for (let start = 0; start + k <= prices.length; start++) {
    const end = start + k;
    const replaced = priceSum[end] - priceSum[start + k / 2];
    const prior = original[end] - original[start];
    bestGain = Math.max(bestGain, replaced - prior);
  }
  return original[prices.length] + bestGain;
}

const maxProfit = solve;
class Solution {
  maxProfit(prices, strategy, k) { return solve(prices, strategy, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProfit };
