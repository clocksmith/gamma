'use strict';

// 1578. Minimum Deletion Cost to Avoid Repeating Letters (Medium).
// Specification: https://leetcode.com/problems/minimum-deletion-cost-to-avoid-repeating-letters/description/
function solve(s, cost) {
  let total = 0;
  for (let i = 1; i < s.length; i++) {
    if (s[i] === s[i - 1]) {
      if (cost[i] < cost[i - 1]) { total += cost[i]; cost[i] = cost[i - 1]; }
      else total += cost[i - 1];
    }
  }
  return total;
}
const minCost = solve;
class Solution { minCost(s, cost) { return solve(s, cost); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCost };
