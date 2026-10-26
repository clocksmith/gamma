'use strict';

// 867. Transpose Matrix (Easy).
// Specification: https://leetcode.com/problems/transpose-matrix/description/
// O(m * n) time and space; allocate independent rows for the transposed result.
function solve(matrix) {
  const rows = matrix.length;
  const columns = matrix[0].length;
  const result = Array.from({ length: columns }, () => new Array(rows));
  for (let row = 0; row < rows; row++) {
    for (let column = 0; column < columns; column++) result[column][row] = matrix[row][column];
  }
  return result;
}

const transpose = solve;
class Solution {
  transpose(matrix) { return solve(matrix); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, transpose };
