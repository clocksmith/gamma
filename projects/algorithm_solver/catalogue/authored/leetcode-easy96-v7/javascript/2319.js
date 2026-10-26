'use strict';

// 2319. Check if Matrix Is X-Matrix (Easy).
// Specification: https://leetcode.com/problems/check-if-matrix-is-x-matrix/description/
// O(n^2) time, O(1) space; exactly the two diagonals must be nonzero; preserve grid.
function solve(grid) {
  const size = grid.length;
  for (let row = 0; row < size; row++) {
    for (let column = 0; column < size; column++) {
      const diagonal = row === column || row + column === size - 1;
      if ((grid[row][column] !== 0) !== diagonal) return false;
    }
  }
  return true;
}

const checkXMatrix = solve;
class Solution {
  checkXMatrix(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkXMatrix };
