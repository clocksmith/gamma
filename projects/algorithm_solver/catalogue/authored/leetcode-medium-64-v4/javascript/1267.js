'use strict';

// 1267. Count Servers that Communicate: count occupied rows and columns before identifying isolated servers.
// O(r * c) time and O(r + c) auxiliary space; inputs are read-only.
function solve(grid) {
  const rows = grid.length;
  const cols = grid[0].length;
  const rowCount = new Int32Array(rows);
  const colCount = new Int32Array(cols);
  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      if (grid[row][col]) {
        rowCount[row] += 1;
        colCount[col] += 1;
      }
    }
  }
  let count = 0;
  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      if (grid[row][col] && (rowCount[row] > 1 || colCount[col] > 1)) count += 1;
    }
  }
  return count;
}

const countServers = solve;
class Solution {
  countServers(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countServers };
