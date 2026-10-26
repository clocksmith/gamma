'use strict';

// 1260. Shift 2D Grid (Easy).
// Specification: https://leetcode.com/problems/shift-2d-grid/description/
// O(m * n) time and result space; preserve grid and row identities.
function solve(grid, k) {
  const rows = grid.length;
  const columns = grid[0].length;
  const size = rows * columns;
  const shift = k % size;
  const result = Array.from({ length: rows }, () => new Array(columns));
  for (let row = 0; row < rows; row++) {
    for (let column = 0; column < columns; column++) {
      const target = (row * columns + column + shift) % size;
      result[Math.floor(target / columns)][target % columns] = grid[row][column];
    }
  }
  return result;
}

const shiftGrid = solve;
class Solution {
  shiftGrid(grid, k) { return solve(grid, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, shiftGrid };
