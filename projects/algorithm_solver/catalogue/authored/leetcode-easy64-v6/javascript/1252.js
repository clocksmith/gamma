'use strict';

// 1252. Cells with Odd Values in a Matrix (Easy).
// Specification: https://leetcode.com/problems/cells-with-odd-values-in-a-matrix/description/
// O(m + n + q) time, O(m + n) space; q = len(indices); preserve inputs.
function solve(m, n, indices) {
  const rows = new Array(m).fill(false);
  const columns = new Array(n).fill(false);
  for (const [row, column] of indices) {
    rows[row] = !rows[row];
    columns[column] = !columns[column];
  }
  let oddRows = 0;
  let oddColumns = 0;
  for (const odd of rows) if (odd) oddRows++;
  for (const odd of columns) if (odd) oddColumns++;
  return oddRows * (n - oddColumns) + (m - oddRows) * oddColumns;
}

const oddCells = solve;
class Solution {
  oddCells(m, n, indices) { return solve(m, n, indices); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, oddCells };
