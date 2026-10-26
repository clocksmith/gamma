'use strict';

// 1582. Special Positions in a Binary Matrix (Easy).
// Specification: https://leetcode.com/problems/special-positions-in-a-binary-matrix/description/
// O(m * n) time, O(m + n) space; preserve mat and its rows.
function solve(mat) {
  const rows = mat.length;
  const columns = mat[0].length;
  const rowCounts = new Array(rows).fill(0);
  const columnCounts = new Array(columns).fill(0);
  for (let row = 0; row < rows; row++) {
    for (let column = 0; column < columns; column++) {
      rowCounts[row] += mat[row][column];
      columnCounts[column] += mat[row][column];
    }
  }
  let result = 0;
  for (let row = 0; row < rows; row++) {
    if (rowCounts[row] !== 1) continue;
    for (let column = 0; column < columns; column++) {
      if (mat[row][column] === 1 && columnCounts[column] === 1) result++;
    }
  }
  return result;
}

const numSpecial = solve;
class Solution {
  numSpecial(mat) { return solve(mat); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numSpecial };
