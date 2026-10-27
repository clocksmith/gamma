'use strict';

// 3958. Minimum Cost to Split into Ones II.
// Specification: https://leetcode.com/problems/minimum-cost-to-split-into-ones-ii/description/
// O(1) time and space; each unordered pair of final ones is separated exactly once. Input is preserved. Under n <= 50000000 the JavaScript integer product is exact.
function solve(n) {
  return n * (n - 1) / 2;
}

const minCost = solve;
class Solution {
  minCost(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCost };
