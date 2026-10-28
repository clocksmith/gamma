'use strict';

// 2711. Difference of Number of Distinct Values on Diagonals (Medium).
// Specification: https://leetcode.com/problems/difference-of-number-of-distinct-values-on-diagonals/description/
function solve(grid) {
  const m = grid.length; const n = grid[0].length;
  const answer = Array.from({ length: m }, () => new Array(n).fill(0));
  for (let r = 0; r < m; r++) {
    for (let c = 0; c < n; c++) {
      const topLeft = new Set();
      for (let i = r - 1, j = c - 1; i >= 0 && j >= 0; i--, j--) topLeft.add(grid[i][j]);
      const bottomRight = new Set();
      for (let i = r + 1, j = c + 1; i < m && j < n; i++, j++) bottomRight.add(grid[i][j]);
      answer[r][c] = Math.abs(topLeft.size - bottomRight.size);
    }
  }
  return answer;
}
const differenceOfDistinctValues = solve;
class Solution { differenceOfDistinctValues(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, differenceOfDistinctValues };
