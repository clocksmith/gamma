'use strict';

// 1572. Matrix Diagonal Sum (Easy).
// Specification: https://leetcode.com/problems/matrix-diagonal-sum/description/
// O(n) time, O(1) space; count the center once; preserve mat and its rows.
function solve(mat) {
  const size = mat.length;
  let result = 0;
  for (let row = 0; row < size; row++) {
    result += mat[row][row];
    const otherColumn = size - row - 1;
    if (otherColumn !== row) result += mat[row][otherColumn];
  }
  return result;
}

const diagonalSum = solve;
class Solution {
  diagonalSum(mat) { return solve(mat); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, diagonalSum };
