'use strict';

// 892. Surface Area of 3D Shapes (Easy).
// Specification: https://leetcode.com/problems/surface-area-of-3d-shapes/description/
function solve(grid) {
  const rows = grid.length; const cols = grid[0].length;
  let area = 0;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const v = grid[r][c];
      if (v > 0) area += 4 * v + 2;
      if (r + 1 < rows) area -= 2 * Math.min(v, grid[r + 1][c]);
      if (c + 1 < cols) area -= 2 * Math.min(v, grid[r][c + 1]);
    }
  }
  return area;
}
const surfaceArea = solve;
class Solution { surfaceArea(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, surfaceArea };
