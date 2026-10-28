'use strict';

// 885. Spiral Matrix III (Medium).
// Specification: https://leetcode.com/problems/spiral-matrix-iii/description/
function solve(rows, cols, rStart, cStart) {
  const result = [];
  const dirs = [[0, 1], [1, 0], [0, -1], [-1, 0]];
  let r = rStart; let c = cStart; let step = 1; let dir = 0;
  result.push([r, c]);
  while (result.length < rows * cols) {
    for (let repeat = 0; repeat < 2; repeat++) {
      for (let i = 0; i < step; i++) {
        r += dirs[dir][0]; c += dirs[dir][1];
        if (r >= 0 && r < rows && c >= 0 && c < cols) result.push([r, c]);
      }
      dir = (dir + 1) % 4;
    }
    step++;
  }
  return result;
}
const spiralMatrixIII = solve;
class Solution { spiralMatrixIII(rows, cols, rStart, cStart) { return solve(rows, cols, rStart, cStart); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, spiralMatrixIII };
