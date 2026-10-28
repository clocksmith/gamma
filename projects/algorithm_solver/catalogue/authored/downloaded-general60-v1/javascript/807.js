'use strict';

// 807. Max Increase to Keep City Skyline (Medium).
// Specification: https://leetcode.com/problems/max-increase-to-keep-city-skyline/description/
function solve(grid) {
  const rows = grid.length; const cols = grid[0].length;
  const rowMax = grid.map((row) => Math.max(...row));
  const colMax = [];
  for (let c = 0; c < cols; c++) { let best = 0; for (let r = 0; r < rows; r++) best = Math.max(best, grid[r][c]); colMax.push(best); }
  let total = 0;
  for (let r = 0; r < rows; r++) { for (let c = 0; c < cols; c++) total += Math.min(rowMax[r], colMax[c]) - grid[r][c]; }
  return total;
}
const maxIncreaseKeepingSkyline = solve;
class Solution { maxIncreaseKeepingSkyline(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxIncreaseKeepingSkyline };
