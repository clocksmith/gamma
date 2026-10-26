'use strict';

// 1289. Minimum Falling Path Sum II: two row minima; O(n^2) time and O(n) space. Inputs are preserved.

function solve(grid) {
  let best = grid[0].slice();
  for (let row = 1; row < grid.length; row += 1) {
    let first = Infinity;
    let second = Infinity;
    let firstColumn = -1;
    for (let column = 0; column < best.length; column += 1) {
      if (best[column] < first) {
        second = first;
        first = best[column];
        firstColumn = column;
      } else if (best[column] < second) second = best[column];
    }
    best = grid[row].map((value, column) => value + (column === firstColumn ? second : first));
  }
  return Math.min(...best);
}

const minFallingPathSum = solve;
class Solution {
  minFallingPathSum(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minFallingPathSum };
