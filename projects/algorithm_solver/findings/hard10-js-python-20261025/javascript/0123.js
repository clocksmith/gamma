/**
 * 123. Best Time to Buy and Sell Stock III (Hard).
 * Fresh candidate authored in this conversation; no repository solution copied.
 * Specification: https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iii/description/
 * Canonical API: solve(prices); native alias: maxProfit(prices).
 * Inputs are preserved. Gamma independent qualification is pending.
 */
'use strict';

function solve(prices) {
  let firstBuy = -Infinity;
  let firstSell = 0;
  let secondBuy = -Infinity;
  let secondSell = 0;
  for (const price of prices) {
    // Reverse order keeps every transition on the previous day's state.
    secondSell = Math.max(secondSell, secondBuy + price);
    secondBuy = Math.max(secondBuy, firstSell - price);
    firstSell = Math.max(firstSell, firstBuy + price);
    firstBuy = Math.max(firstBuy, -price);
  }
  return secondSell;
}

function maxProfit(prices) {
  return solve(prices);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, maxProfit };
}
