'use strict';

// 48. Rotate Image (Medium).
// Specification: https://leetcode.com/problems/rotate-image/description/
function solve(matrix) {
  const n = matrix.length;
  const result = Array.from({ length: n }, () => new Array(n));
  for (let r = 0; r < n; r++) { for (let c = 0; c < n; c++) result[c][n - 1 - r] = matrix[r][c]; }
  return result;
}
const rotate = solve;
class Solution { rotate(matrix) { return solve(matrix); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, rotate };
