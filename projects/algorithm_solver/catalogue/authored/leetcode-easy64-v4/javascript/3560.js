'use strict';

// 3560. Find Minimum Log Transportation Cost (Easy).
// Specification: https://leetcode.com/problems/find-minimum-log-transportation-cost/description/
// O(1) time and space; feasible inputs require at most one cut; products use exact integers.
function solve(n, m, k) {
  const excess = Math.max(0, Math.max(n, m) - k);
  return excess * k;
}

const minCuttingCost = solve;
class Solution {
  minCuttingCost(n, m, k) { return solve(n, m, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCuttingCost };
