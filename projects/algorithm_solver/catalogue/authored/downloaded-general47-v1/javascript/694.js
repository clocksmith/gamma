'use strict';

// 694. Number of Distinct Islands (Medium).
// Specification: https://leetcode.com/problems/number-of-distinct-islands/description/
function solve(grid) {
  const rows = grid.length; const cols = grid[0].length;
  const copy = grid.map((row) => row.slice());
  const shapes = new Set();
  function dfs(r, c, baseR, baseC, cells) {
    if (r < 0 || r >= rows || c < 0 || c >= cols || copy[r][c] !== 1) return;
    copy[r][c] = 0;
    cells.push((r - baseR) + ',' + (c - baseC));
    dfs(r + 1, c, baseR, baseC, cells); dfs(r - 1, c, baseR, baseC, cells); dfs(r, c + 1, baseR, baseC, cells); dfs(r, c - 1, baseR, baseC, cells);
  }
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (copy[r][c] === 1) {
        const cells = [];
        dfs(r, c, r, c, cells);
        cells.sort();
        shapes.add(cells.join(';'));
      }
    }
  }
  return shapes.size;
}
const numDistinctIslands = solve;
class Solution { numDistinctIslands(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numDistinctIslands };
