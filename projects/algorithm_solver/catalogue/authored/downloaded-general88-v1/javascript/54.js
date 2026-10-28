'use strict';

// 54. Spiral Matrix (Medium).
// Specification: https://leetcode.com/problems/spiral-matrix/description/
function solve(matrix) {
  if (matrix.length === 0) return [];
  const result = [];
  let top = 0; let bottom = matrix.length - 1; let left = 0; let right = matrix[0].length - 1;
  while (top <= bottom && left <= right) {
    for (let c = left; c <= right; c++) result.push(matrix[top][c]);
    top++;
    for (let r = top; r <= bottom; r++) result.push(matrix[r][right]);
    right--;
    if (top <= bottom) { for (let c = right; c >= left; c--) result.push(matrix[bottom][c]); bottom--; }
    if (left <= right) { for (let r = bottom; r >= top; r--) result.push(matrix[r][left]); left++; }
  }
  return result;
}
const spiralOrder = solve;
class Solution { spiralOrder(matrix) { return solve(matrix); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, spiralOrder };
