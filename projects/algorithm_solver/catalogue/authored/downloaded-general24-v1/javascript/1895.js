'use strict';

// 1895. Largest Magic Square (Medium).
// Specification: https://leetcode.com/problems/largest-magic-square/description/
function isMagic(grid, top, left, size) {
  let target = 0;
  for (let c = 0; c < size; c++) target += grid[top][left + c];
  for (let r = 0; r < size; r++) {
    let rowSum = 0;
    for (let c = 0; c < size; c++) rowSum += grid[top + r][left + c];
    if (rowSum !== target) return false;
  }
  for (let c = 0; c < size; c++) {
    let colSum = 0;
    for (let r = 0; r < size; r++) colSum += grid[top + r][left + c];
    if (colSum !== target) return false;
  }
  let diag1 = 0; let diag2 = 0;
  for (let i = 0; i < size; i++) { diag1 += grid[top + i][left + i]; diag2 += grid[top + i][left + size - 1 - i]; }
  return diag1 === target && diag2 === target;
}
function solve(grid) {
  const rows = grid.length; const cols = grid[0].length;
  for (let size = Math.min(rows, cols); size >= 1; size--) {
    for (let top = 0; top + size <= rows; top++) {
      for (let left = 0; left + size <= cols; left++) {
        if (isMagic(grid, top, left, size)) return size;
      }
    }
  }
  return 1;
}
const largestMagicSquare = solve;
class Solution { largestMagicSquare(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestMagicSquare };
