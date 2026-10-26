'use strict';

// 1380. Lucky Numbers in a Matrix (Easy).
// Specification: https://leetcode.com/problems/lucky-numbers-in-a-matrix/description/
// O(rows * columns) time, O(rows + columns) auxiliary space; preserve matrix.
function solve(matrix) {
  const rows = matrix.length;
  const columns = matrix[0].length;
  const rowMinima = new Array(rows).fill(Infinity);
  const columnMaxima = new Array(columns).fill(-Infinity);
  for (let row = 0; row < rows; row++) {
    for (let column = 0; column < columns; column++) {
      const value = matrix[row][column];
      rowMinima[row] = Math.min(rowMinima[row], value);
      columnMaxima[column] = Math.max(columnMaxima[column], value);
    }
  }
  const result = [];
  for (let row = 0; row < rows; row++) {
    for (let column = 0; column < columns; column++) {
      const value = matrix[row][column];
      if (value === rowMinima[row] && value === columnMaxima[column]) result.push(value);
    }
  }
  return result;
}

const luckyNumbers = solve;
class Solution {
  luckyNumbers(matrix) { return solve(matrix); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, luckyNumbers };
