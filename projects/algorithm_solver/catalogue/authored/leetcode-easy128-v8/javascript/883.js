'use strict';

// 883. Projection Area of 3D Shapes (Easy).
// Specification: https://leetcode.com/problems/projection-area-of-3d-shapes/description/
// O(n^2) time, O(1) auxiliary space; count occupied cells and maxima on both axes.
function solve(grid) {
  let area = 0;
  for (let index = 0; index < grid.length; index++) {
    let rowMaximum = 0;
    let columnMaximum = 0;
    for (let other = 0; other < grid.length; other++) {
      if (grid[index][other] > 0) area++;
      rowMaximum = Math.max(rowMaximum, grid[index][other]);
      columnMaximum = Math.max(columnMaximum, grid[other][index]);
    }
    area += rowMaximum + columnMaximum;
  }
  return area;
}

const projectionArea = solve;
class Solution {
  projectionArea(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, projectionArea };
