'use strict';

// 2133. Check if Every Row and Column Contains All Numbers (Easy).
// Specification: https://leetcode.com/problems/check-if-every-row-and-column-contains-all-numbers/description/
// O(n^2) time, O(n) space; values are in 1..n; preserve matrix and row identities.
function solve(matrix) {
  const size = matrix.length;
  for (let index = 0; index < size; index++) {
    const row = new Set();
    const column = new Set();
    for (let other = 0; other < size; other++) {
      row.add(matrix[index][other]);
      column.add(matrix[other][index]);
    }
    if (row.size !== size || column.size !== size) return false;
  }
  return true;
}

const checkValid = solve;
class Solution {
  checkValid(matrix) { return solve(matrix); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkValid };
