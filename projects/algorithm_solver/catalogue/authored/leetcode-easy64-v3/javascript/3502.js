'use strict';

// 3502. Minimum Cost to Reach Every Position (Easy).
// Specification: https://leetcode.com/problems/minimum-cost-to-reach-every-position/description/
// O(n) time and output space; a prefix minimum permits free backward swaps.
function solve(cost) {
  const result = [];
  let cheapest = Infinity;
  for (const value of cost) {
    cheapest = Math.min(cheapest, value);
    result.push(cheapest);
  }
  return result;
}

const minCosts = solve;
class Solution {
  minCosts(cost) { return solve(cost); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCosts };
