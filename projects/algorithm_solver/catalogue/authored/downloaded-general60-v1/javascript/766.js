'use strict';

// 766. Toeplitz Matrix (Easy).
// Specification: https://leetcode.com/problems/toeplitz-matrix/description/
function solve(matrix) {
  for (let r = 1; r < matrix.length; r++) {
    for (let c = 1; c < matrix[0].length; c++) {
      if (matrix[r][c] !== matrix[r - 1][c - 1]) return false;
    }
  }
  return true;
}
const isToeplitzMatrix = solve;
class Solution { isToeplitzMatrix(matrix) { return solve(matrix); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isToeplitzMatrix };
