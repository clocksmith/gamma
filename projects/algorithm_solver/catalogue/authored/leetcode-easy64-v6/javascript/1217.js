'use strict';

// 1217. Minimum Cost to Move Chips to The Same Position (Easy).
// Specification: https://leetcode.com/problems/minimum-cost-to-move-chips-to-the-same-position/description/
// O(n) time, O(1) space; preserve position.
function solve(position) {
  let oddCount = 0;
  for (const value of position) oddCount += value % 2;
  return Math.min(oddCount, position.length - oddCount);
}

const minCostToMoveChips = solve;
class Solution {
  minCostToMoveChips(position) { return solve(position); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCostToMoveChips };
