'use strict';

// 240. Search a 2D Matrix II (Medium).
// Specification: https://leetcode.com/problems/search-a-2d-matrix-ii/description/
function solve(matrix, target) {
  if (matrix.length === 0) return false;
  let row = 0; let col = matrix[0].length - 1;
  while (row < matrix.length && col >= 0) {
    const value = matrix[row][col];
    if (value === target) return true;
    if (value > target) col--;
    else row++;
  }
  return false;
}
const searchMatrix = solve;
class Solution { searchMatrix(matrix, target) { return solve(matrix, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, searchMatrix };
