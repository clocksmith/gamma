'use strict';

// 2639. Find the Width of Columns of a Grid (Easy).
// Specification: https://leetcode.com/problems/find-the-width-of-columns-of-a-grid/description/
// O(r * c * d) time, O(c + d) space; preserve grid; d is maximum digit width.
function solve(grid) {
  const widths = new Array(grid[0].length).fill(0);
  for (const row of grid) {
    for (let column = 0; column < row.length; column++) {
      widths[column] = Math.max(widths[column], String(row[column]).length);
    }
  }
  return widths;
}

const findColumnWidth = solve;
class Solution {
  findColumnWidth(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findColumnWidth };
