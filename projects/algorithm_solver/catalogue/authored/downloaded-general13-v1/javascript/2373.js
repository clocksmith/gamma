'use strict';

// 2373. Largest Local Values in a Matrix (Easy).
// Specification: https://leetcode.com/problems/largest-local-values-in-a-matrix/description/
function solve(grid) {
  const n = grid.length; const out = [];
  for (let i = 0; i < n - 2; i++) {
    const row = [];
    for (let j = 0; j < n - 2; j++) {
      let best = -Infinity;
      for (let di = 0; di < 3; di++) for (let dj = 0; dj < 3; dj++) best = Math.max(best, grid[i + di][j + dj]);
      row.push(best);
    }
    out.push(row);
  }
  return out;
}
const largestLocal = solve;
class Solution { largestLocal(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestLocal };
