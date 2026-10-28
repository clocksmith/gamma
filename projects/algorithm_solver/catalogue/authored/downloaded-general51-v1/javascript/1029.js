'use strict';

// 1029. Two City Scheduling (Medium).
// Specification: https://leetcode.com/problems/two-city-scheduling/description/
function solve(costs) {
  const sorted = costs.slice().sort((a, b) => (a[0] - a[1]) - (b[0] - b[1]));
  let total = 0;
  const half = sorted.length / 2;
  for (let i = 0; i < sorted.length; i++) total += i < half ? sorted[i][0] : sorted[i][1];
  return total;
}
const twoCitySchedCost = solve;
class Solution { twoCitySchedCost(costs) { return solve(costs); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, twoCitySchedCost };
