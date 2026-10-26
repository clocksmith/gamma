'use strict';

// 2661. First Completely Painted Row or Column: map values to cells and count painted cells per row and column.
// O(r * c) time and O(r * c) auxiliary space; inputs are read-only.
function solve(arr, mat) {
  const rows = mat.length;
  const columns = mat[0].length;
  const positions = new Int32Array(rows * columns + 1);
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) positions[mat[row][column]] = row * columns + column;
  }
  const rowCounts = new Int32Array(rows);
  const columnCounts = new Int32Array(columns);
  for (let index = 0; index < arr.length; index += 1) {
    const position = positions[arr[index]];
    const row = Math.floor(position / columns);
    const column = position % columns;
    rowCounts[row] += 1;
    columnCounts[column] += 1;
    if (rowCounts[row] === columns || columnCounts[column] === rows) return index;
  }
  return -1;
}

const firstCompleteIndex = solve;
class Solution {
  firstCompleteIndex(arr, mat) { return solve(arr, mat); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, firstCompleteIndex };
