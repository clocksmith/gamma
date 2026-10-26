'use strict';

// 1975. Maximum Matrix Sum: preserve negative parity while placing any unavoidable negative sign on the smallest magnitude.
// O(n^2) time and O(1) auxiliary space; inputs are read-only.
function solve(matrix) {
  let total = 0;
  let negatives = 0;
  let smallest = Math.abs(matrix[0][0]);
  for (const row of matrix) {
    for (const value of row) {
      const magnitude = Math.abs(value);
      total += magnitude;
      smallest = Math.min(smallest, magnitude);
      if (value < 0) negatives += 1;
    }
  }
  return negatives % 2 ? total - 2 * smallest : total;
}

const maxMatrixSum = solve;
class Solution {
  maxMatrixSum(matrix) { return solve(matrix); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxMatrixSum };
