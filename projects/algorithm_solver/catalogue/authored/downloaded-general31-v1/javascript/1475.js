'use strict';

// 1475. Final Prices With a Special Discount in a Shop (Easy).
// Specification: https://leetcode.com/problems/final-prices-with-a-special-discount-in-a-shop/description/
function solve(prices) {
  const result = prices.slice();
  const stack = [];
  for (let i = 0; i < prices.length; i++) {
    while (stack.length > 0 && prices[stack[stack.length - 1]] >= prices[i]) {
      const index = stack.pop();
      result[index] -= prices[i];
    }
    stack.push(i);
  }
  return result;
}
const finalPrices = solve;
class Solution { finalPrices(prices) { return solve(prices); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, finalPrices };
