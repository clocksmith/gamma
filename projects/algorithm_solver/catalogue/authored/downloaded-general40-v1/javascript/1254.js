'use strict';

// 1254. Number of Closed Islands (Medium).
// Specification: https://leetcode.com/problems/number-of-closed-islands/description/
function solve(grid) {
  const rows = grid.length; const cols = grid[0].length;
  const copy = grid.map((row) => row.slice());
  function dfs(r, c) {
    if (r < 0 || r >= rows || c < 0 || c >= cols || copy[r][c] !== 0) return;
    copy[r][c] = 1;
    dfs(r + 1, c); dfs(r - 1, c); dfs(r, c + 1); dfs(r, c - 1);
  }
  for (let r = 0; r < rows; r++) { dfs(r, 0); dfs(r, cols - 1); }
  for (let c = 0; c < cols; c++) { dfs(0, c); dfs(rows - 1, c); }
  let count = 0;
  for (let r = 0; r < rows; r++) { for (let c = 0; c < cols; c++) { if (copy[r][c] === 0) { count++; dfs(r, c); } } }
  return count;
}
const closedIsland = solve;
class Solution { closedIsland(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, closedIsland };
