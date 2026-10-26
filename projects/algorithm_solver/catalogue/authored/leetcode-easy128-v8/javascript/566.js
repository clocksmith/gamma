'use strict';

// 566. Reshape the Matrix (Easy).
// Specification: https://leetcode.com/problems/reshape-the-matrix/description/
// O(m * n) time and space; row-major reshape, returning fresh rows even when unchanged.
function solve(mat, r, c) {
  const rows = mat.length;
  const columns = mat[0].length;
  if (rows * columns !== r * c) return mat.map(row => row.slice());
  const result = Array.from({ length: r }, () => new Array(c));
  for (let index = 0; index < rows * columns; index++) {
    result[Math.floor(index / c)][index % c] = mat[Math.floor(index / columns)][index % columns];
  }
  return result;
}

const matrixReshape = solve;
class Solution {
  matrixReshape(mat, r, c) { return solve(mat, r, c); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, matrixReshape };
