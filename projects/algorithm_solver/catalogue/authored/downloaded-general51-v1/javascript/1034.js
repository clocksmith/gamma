'use strict';

// 1034. Coloring A Border (Medium).
// Specification: https://leetcode.com/problems/coloring-a-border/description/
function solve(grid, row, col, color) {
  const rows = grid.length; const cols = grid[0].length;
  const original = grid[row][col];
  const result = grid.map((line) => line.slice());
  const visited = new Set();
  function dfs(r, c) {
    const key = r + ',' + c;
    if (r < 0 || r >= rows || c < 0 || c >= cols || grid[r][c] !== original || visited.has(key)) return;
    visited.add(key);
    const isBorder = r === 0 || r === rows - 1 || c === 0 || c === cols - 1 || grid[r - 1][c] !== original || grid[r + 1][c] !== original || grid[r][c - 1] !== original || grid[r][c + 1] !== original;
    if (isBorder) result[r][c] = color;
    dfs(r + 1, c); dfs(r - 1, c); dfs(r, c + 1); dfs(r, c - 1);
  }
  dfs(row, col);
  return result;
}
const colorBorder = solve;
class Solution { colorBorder(grid, row, col, color) { return solve(grid, row, col, color); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, colorBorder };
