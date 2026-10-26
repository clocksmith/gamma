'use strict';

// 1605. Find Valid Matrix Given Row and Column Sums: satisfy one residual row or column at every placement.
// O(r * c + r + c) time and O(r + c) auxiliary space excluding the result; inputs are read-only.
function solve(rowSum, colSum) {
  const rows = rowSum.length;
  const cols = colSum.length;
  const rowNeed = rowSum.slice();
  const colNeed = colSum.slice();
  const result = Array.from({ length: rows }, () => new Array(cols).fill(0));
  let row = 0;
  let col = 0;
  while (row < rows && col < cols) {
    const value = Math.min(rowNeed[row], colNeed[col]);
    result[row][col] = value;
    rowNeed[row] -= value;
    colNeed[col] -= value;
    const rowDone = rowNeed[row] === 0;
    const colDone = colNeed[col] === 0;
    if (rowDone) row += 1;
    if (colDone) col += 1;
  }
  return result;
}

const restoreMatrix = solve;
class Solution {
  restoreMatrix(rowSum, colSum) { return solve(rowSum, colSum); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, restoreMatrix };
