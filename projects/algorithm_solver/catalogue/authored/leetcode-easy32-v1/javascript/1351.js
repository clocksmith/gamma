'use strict';

// 1351. Count Negative Numbers in a Sorted Matrix (Easy).
// Specification: https://leetcode.com/problems/count-negative-numbers-in-a-sorted-matrix/description/
// O(rows + columns) time, O(1) auxiliary space. Preserve grid and its rows.
function solve(grid) {
  const columns = grid[0].length;
  let row = grid.length - 1;
  let column = 0;
  let count = 0;
  while (row >= 0 && column < columns) {
    if (grid[row][column] < 0) {
      count += columns - column;
      row--;
    } else {
      column++;
    }
  }
  return count;
}

const countNegatives = solve;
class Solution {
  countNegatives(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countNegatives };
