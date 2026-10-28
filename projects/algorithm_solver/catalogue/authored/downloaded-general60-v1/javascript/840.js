'use strict';

// 840. Magic Squares In Grid (Medium).
// Specification: https://leetcode.com/problems/magic-squares-in-grid/description/
function isMagic(grid, r, c) {
  const values = [];
  for (let i = 0; i < 3; i++) { for (let j = 0; j < 3; j++) values.push(grid[r + i][c + j]); }
  if ([...values].sort((a, b) => a - b).join(',') !== '1,2,3,4,5,6,7,8,9') return false;
  for (let i = 0; i < 3; i++) {
    if (grid[r + i][c] + grid[r + i][c + 1] + grid[r + i][c + 2] !== 15) return false;
    if (grid[r][c + i] + grid[r + 1][c + i] + grid[r + 2][c + i] !== 15) return false;
  }
  if (grid[r][c] + grid[r + 1][c + 1] + grid[r + 2][c + 2] !== 15) return false;
  if (grid[r][c + 2] + grid[r + 1][c + 1] + grid[r + 2][c] !== 15) return false;
  return true;
}
function solve(grid) {
  let count = 0;
  for (let r = 0; r + 2 < grid.length; r++) {
    for (let c = 0; c + 2 < grid[0].length; c++) { if (isMagic(grid, r, c)) count++; }
  }
  return count;
}
const numMagicSquaresInside = solve;
class Solution { numMagicSquaresInside(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numMagicSquaresInside };
