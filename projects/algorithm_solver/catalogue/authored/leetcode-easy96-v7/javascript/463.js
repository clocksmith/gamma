'use strict';

// 463. Island Perimeter (Easy).
// Specification: https://leetcode.com/problems/island-perimeter/description/
// O(rows * columns) time, O(1) space; subtract shared edges once; preserve grid and rows.
function solve(grid) {
  let perimeter = 0;
  for (let row = 0; row < grid.length; row++) {
    for (let column = 0; column < grid[row].length; column++) {
      if (grid[row][column] !== 1) continue;
      perimeter += 4;
      if (row > 0 && grid[row - 1][column] === 1) perimeter -= 2;
      if (column > 0 && grid[row][column - 1] === 1) perimeter -= 2;
    }
  }
  return perimeter;
}

const islandPerimeter = solve;
class Solution {
  islandPerimeter(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, islandPerimeter };
