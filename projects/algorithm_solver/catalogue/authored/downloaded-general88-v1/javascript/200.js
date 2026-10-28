'use strict';

// 200. Number of Islands (Medium).
// Specification: https://leetcode.com/problems/number-of-islands/description/
function solve(grid) {
  const rows = grid.length; const cols = grid[0].length;
  const copy = grid.map((row) => row.slice());
  function dfs(r, c) {
    if (r < 0 || r >= rows || c < 0 || c >= cols || copy[r][c] !== '1') return;
    copy[r][c] = '0';
    dfs(r + 1, c); dfs(r - 1, c); dfs(r, c + 1); dfs(r, c - 1);
  }
  let count = 0;
  for (let r = 0; r < rows; r++) { for (let c = 0; c < cols; c++) { if (copy[r][c] === '1') { count++; dfs(r, c); } } }
  return count;
}
const numIslands = solve;
class Solution { numIslands(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numIslands };
