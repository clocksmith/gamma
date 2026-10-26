'use strict';

// 2144. Minimum Cost of Buying Candies With Discount (Easy).
// Specification: https://leetcode.com/problems/minimum-cost-of-buying-candies-with-discount/description/
// O(n log n) time, O(n) space; make every third candy free in descending-price order; preserve cost.
function solve(cost) {
  const prices = cost.slice().sort((a, b) => b - a);
  let total = 0;
  for (let index = 0; index < prices.length; index++) {
    if (index % 3 !== 2) total += prices[index];
  }
  return total;
}

const minimumCost = solve;
class Solution {
  minimumCost(cost) { return solve(cost); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumCost };
