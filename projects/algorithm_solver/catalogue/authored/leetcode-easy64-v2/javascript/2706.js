'use strict';

// 2706. Buy Two Chocolates (Easy).
// Specification: https://leetcode.com/problems/buy-two-chocolates/description/
// O(n) time, O(1) space; find two distinct purchases without sorting prices.
function solve(prices, money) {
  let first = Infinity;
  let second = Infinity;
  for (const price of prices) {
    if (price < first) {
      second = first;
      first = price;
    } else if (price < second) {
      second = price;
    }
  }
  const cost = first + second;
  return cost <= money ? money - cost : money;
}

const buyChoco = solve;
class Solution {
  buyChoco(prices, money) { return solve(prices, money); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, buyChoco };
