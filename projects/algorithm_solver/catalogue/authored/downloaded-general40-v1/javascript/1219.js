'use strict';

// 1219. Path with Maximum Gold (Medium).
// Specification: https://leetcode.com/problems/path-with-maximum-gold/description/
function solve(grid) {
  const rows = grid.length; const cols = grid[0].length;
  let best = 0;
  function dfs(r, c, total) {
    best = Math.max(best, total);
    const saved = grid[r][c];
    grid[r][c] = 0;
    const directions = [[1, 0], [-1, 0], [0, 1], [0, -1]];
    for (const [dr, dc] of directions) {
      const nr = r + dr; const nc = c + dc;
      if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] > 0) dfs(nr, nc, total + grid[nr][nc]);
    }
    grid[r][c] = saved;
  }
  for (let r = 0; r < rows; r++) { for (let c = 0; c < cols; c++) { if (grid[r][c] > 0) dfs(r, c, grid[r][c]); } }
  return best;
}
const getMaximumGold = solve;
class Solution { getMaximumGold(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getMaximumGold };
