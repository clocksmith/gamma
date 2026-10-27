'use strict';
// 240. Search a 2D Matrix II.
function solve(matrix, target) {
  let row = 0; let column = matrix[0].length - 1;
  while (row < matrix.length && column >= 0) {
    const value = matrix[row][column];
    if (value === target) return true;
    if (value > target) column -= 1; else row += 1;
  }
  return false;
}
const searchMatrix = solve;
class Solution { searchMatrix(matrix, target) { return solve(matrix, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, searchMatrix };
