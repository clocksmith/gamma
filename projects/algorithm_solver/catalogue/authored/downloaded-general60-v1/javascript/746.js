'use strict';

// 746. Min Cost Climbing Stairs (Easy).
// Specification: https://leetcode.com/problems/min-cost-climbing-stairs/description/
function solve(cost) {
  let a = 0; let b = 0;
  for (let i = 2; i <= cost.length; i++) { const next = Math.min(a + cost[i - 2], b + cost[i - 1]); a = b; b = next; }
  return b;
}
const minCostClimbingStairs = solve;
class Solution { minCostClimbingStairs(cost) { return solve(cost); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCostClimbingStairs };
