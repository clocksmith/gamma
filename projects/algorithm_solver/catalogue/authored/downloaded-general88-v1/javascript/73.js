'use strict';

// 73. Set Matrix Zeroes (Medium).
// Specification: https://leetcode.com/problems/set-matrix-zeroes/description/
function solve(matrix) {
  const rows = matrix.length; const cols = matrix[0].length;
  const zeroRows = new Set(); const zeroCols = new Set();
  for (let r = 0; r < rows; r++) { for (let c = 0; c < cols; c++) { if (matrix[r][c] === 0) { zeroRows.add(r); zeroCols.add(c); } } }
  const result = matrix.map((row) => row.slice());
  for (let r = 0; r < rows; r++) { for (let c = 0; c < cols; c++) { if (zeroRows.has(r) || zeroCols.has(c)) result[r][c] = 0; } }
  return result;
}
const setZeroes = solve;
class Solution { setZeroes(matrix) { return solve(matrix); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, setZeroes };
