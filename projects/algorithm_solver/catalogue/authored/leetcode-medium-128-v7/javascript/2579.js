'use strict';

// 2579. Count Total Number of Colored Cells: sum the successive diamond boundaries around the first cell.
// O(1) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(n) {
  return 1 + 2 * n * (n - 1);
}

const coloredCells = solve;
class Solution {
  coloredCells(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, coloredCells };
