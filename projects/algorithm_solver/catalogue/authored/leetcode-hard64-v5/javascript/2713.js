'use strict';

// 2713. Maximum Strictly Increasing Cells in a Matrix. Batch equal values before updating row and column maxima; O(m*n log(m*n)) time and O(m*n) space. Inputs are preserved.

function solve(mat) {
  const rows = mat.length;
  const columns = mat[0].length;
  const cells = [];
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) cells.push([mat[row][column], row, column]);
  }
  cells.sort((a, b) => a[0] - b[0]);
  const rowBest = Array(rows).fill(0);
  const columnBest = Array(columns).fill(0);
  let answer = 0;
  let begin = 0;
  while (begin < cells.length) {
    let end = begin;
    const updates = [];
    while (end < cells.length && cells[end][0] === cells[begin][0]) {
      const [, row, column] = cells[end];
      const length = 1 + Math.max(rowBest[row], columnBest[column]);
      updates.push([row, column, length]);
      answer = Math.max(answer, length);
      end += 1;
    }
    for (const [row, column, length] of updates) {
      rowBest[row] = Math.max(rowBest[row], length);
      columnBest[column] = Math.max(columnBest[column], length);
    }
    begin = end;
  }
  return answer;
}

const maxIncreasingCells = solve;
class Solution {
  maxIncreasingCells(mat) { return solve(mat); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxIncreasingCells };
