'use strict';

// 3127. Make a Square with the Same Color (Easy).
// Specification: https://leetcode.com/problems/make-a-square-with-the-same-color/description/
// O(1) time and space for a 3-by-3 grid; do not modify its cells.
function solve(grid) {
  for (let row = 0; row < 2; row++) {
    for (let column = 0; column < 2; column++) {
      let black = 0;
      for (let rowOffset = 0; rowOffset < 2; rowOffset++) {
        for (let columnOffset = 0; columnOffset < 2; columnOffset++) {
          if (grid[row + rowOffset][column + columnOffset] === 'B') black++;
        }
      }
      if (black !== 2) return true;
    }
  }
  return false;
}

const canMakeSquare = solve;
class Solution {
  canMakeSquare(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canMakeSquare };
