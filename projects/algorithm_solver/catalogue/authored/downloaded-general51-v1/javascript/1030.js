'use strict';

// 1030. Matrix Cells in Distance Order (Easy).
// Specification: https://leetcode.com/problems/matrix-cells-in-distance-order/description/
function solve(rows, cols, rCenter, cCenter) {
  const cells = [];
  for (let r = 0; r < rows; r++) { for (let c = 0; c < cols; c++) cells.push([r, c]); }
  cells.sort((a, b) => (Math.abs(a[0] - rCenter) + Math.abs(a[1] - cCenter)) - (Math.abs(b[0] - rCenter) + Math.abs(b[1] - cCenter)) || a[0] - b[0] || a[1] - b[1]);
  return cells;
}
const allCellsDistOrder = solve;
class Solution { allCellsDistOrder(rows, cols, rCenter, cCenter) { return solve(rows, cols, rCenter, cCenter); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, allCellsDistOrder };
