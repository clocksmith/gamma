'use strict';

// 3239. Minimum Number of Flips to Make Binary Grid Palindromic I (Medium).
// Specification: https://leetcode.com/problems/minimum-number-of-flips-to-make-binary-grid-palindromic-i/description/
function solve(grid) {
  const m = grid.length; const n = grid[0].length;
  let rows = 0; let cols = 0;
  for (let i = 0; i < m; i++)
    for (let j = 0; j < n / 2; j++)
      if (grid[i][j] !== grid[i][n - 1 - j]) rows++;
  for (let j = 0; j < n; j++)
    for (let i = 0; i < m / 2; i++)
      if (grid[i][j] !== grid[m - 1 - i][j]) cols++;
  return Math.min(rows, cols);
}
const minFlips = solve;
class Solution { minFlips(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minFlips };
