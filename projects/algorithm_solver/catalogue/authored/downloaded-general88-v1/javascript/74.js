'use strict';

// 74. Search a 2D Matrix (Medium).
// Specification: https://leetcode.com/problems/search-a-2d-matrix/description/
function solve(matrix, target) {
  const rows = matrix.length; const cols = matrix[0].length;
  let left = 0; let right = rows * cols - 1;
  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    const value = matrix[Math.floor(mid / cols)][mid % cols];
    if (value === target) return true;
    if (value < target) left = mid + 1; else right = mid - 1;
  }
  return false;
}
const searchMatrix = solve;
class Solution { searchMatrix(matrix, target) { return solve(matrix, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, searchMatrix };
