'use strict';

// 3142. Check if Grid Satisfies Conditions (Easy).
// Specification: https://leetcode.com/problems/check-if-grid-satisfies-conditions/description/
function solve(grid) {
  const m = grid.length; const n = grid[0].length;
  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      if (i + 1 < m && grid[i][j] !== grid[i + 1][j]) return false;
      if (j + 1 < n && grid[i][j] === grid[i][j + 1]) return false;
    }
  }
  return true;
}
const satisfiesConditions = solve;
class Solution { satisfiesConditions(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, satisfiesConditions };
