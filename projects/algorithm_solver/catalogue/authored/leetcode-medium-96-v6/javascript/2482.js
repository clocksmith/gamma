'use strict';

// 2482. Difference Between Ones and Zeros in Row and Column: derive each output cell from its row and column one counts.
// O(mn) time and O(m + n) auxiliary space beyond the O(mn) result; inputs are read-only.
function solve(grid) {
  const rows = grid.length;
  const columns = grid[0].length;
  const rowOnes = new Int32Array(rows);
  const columnOnes = new Int32Array(columns);
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      rowOnes[row] += grid[row][column];
      columnOnes[column] += grid[row][column];
    }
  }
  return Array.from({ length: rows }, (_, row) =>
    Array.from({ length: columns }, (_, column) =>
      2 * (rowOnes[row] + columnOnes[column]) - rows - columns));
}

const onesMinusZeros = solve;
class Solution {
  onesMinusZeros(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, onesMinusZeros };
