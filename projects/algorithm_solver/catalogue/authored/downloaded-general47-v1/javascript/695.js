'use strict';

// 695. Max Area of Island (Medium).
// Specification: https://leetcode.com/problems/max-area-of-island/description/
function solve(grid) {
  const rows = grid.length; const cols = grid[0].length;
  const copy = grid.map((row) => row.slice());
  function dfs(r, c) {
    if (r < 0 || r >= rows || c < 0 || c >= cols || copy[r][c] !== 1) return 0;
    copy[r][c] = 0;
    return 1 + dfs(r + 1, c) + dfs(r - 1, c) + dfs(r, c + 1) + dfs(r, c - 1);
  }
  let best = 0;
  for (let r = 0; r < rows; r++) { for (let c = 0; c < cols; c++) { if (copy[r][c] === 1) best = Math.max(best, dfs(r, c)); } }
  return best;
}
const maxAreaOfIsland = solve;
class Solution { maxAreaOfIsland(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxAreaOfIsland };
