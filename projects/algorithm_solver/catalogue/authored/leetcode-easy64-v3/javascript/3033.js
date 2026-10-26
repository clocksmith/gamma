'use strict';

// 3033. Modify the Matrix (Easy).
// Specification: https://leetcode.com/problems/modify-the-matrix/description/
// O(rows * columns) time and output space; return fresh rows and preserve matrix.
function solve(matrix) {
  const result = matrix.map(row => row.slice());
  for (let column = 0; column < matrix[0].length; column++) {
    let maximum = -1;
    for (let row = 0; row < matrix.length; row++) {
      maximum = Math.max(maximum, matrix[row][column]);
    }
    for (let row = 0; row < matrix.length; row++) {
      if (result[row][column] === -1) result[row][column] = maximum;
    }
  }
  return result;
}

const modifiedMatrix = solve;
class Solution {
  modifiedMatrix(matrix) { return solve(matrix); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, modifiedMatrix };
