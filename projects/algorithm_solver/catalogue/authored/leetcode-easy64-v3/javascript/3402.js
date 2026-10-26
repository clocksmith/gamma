'use strict';

// 3402. Minimum Operations to Make Columns Strictly Increasing (Easy).
// Specification: https://leetcode.com/problems/minimum-operations-to-make-columns-strictly-increasing/description/
// O(rows * columns) time, O(1) space; track adjusted heights without modifying grid.
function solve(grid) {
  let operations = 0;
  for (let column = 0; column < grid[0].length; column++) {
    let previous = grid[0][column];
    for (let row = 1; row < grid.length; row++) {
      const adjusted = Math.max(grid[row][column], previous + 1);
      operations += adjusted - grid[row][column];
      previous = adjusted;
    }
  }
  return operations;
}

const minimumOperations = solve;
class Solution {
  minimumOperations(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumOperations };
