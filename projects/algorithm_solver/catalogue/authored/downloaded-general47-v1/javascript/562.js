'use strict';

// 562. Longest Line of Consecutive One in Matrix (Medium).
// Specification: https://leetcode.com/problems/longest-line-of-consecutive-one-in-matrix/description/
function solve(mat) {
  const rows = mat.length; const cols = mat[0].length;
  const horizontal = Array.from({ length: rows }, () => new Array(cols).fill(0));
  const vertical = Array.from({ length: rows }, () => new Array(cols).fill(0));
  const diagonal = Array.from({ length: rows }, () => new Array(cols).fill(0));
  const antiDiagonal = Array.from({ length: rows }, () => new Array(cols).fill(0));
  let best = 0;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (mat[r][c] === 1) {
        horizontal[r][c] = (c > 0 ? horizontal[r][c - 1] : 0) + 1;
        vertical[r][c] = (r > 0 ? vertical[r - 1][c] : 0) + 1;
        diagonal[r][c] = (r > 0 && c > 0 ? diagonal[r - 1][c - 1] : 0) + 1;
        antiDiagonal[r][c] = (r > 0 && c + 1 < cols ? antiDiagonal[r - 1][c + 1] : 0) + 1;
        best = Math.max(best, horizontal[r][c], vertical[r][c], diagonal[r][c], antiDiagonal[r][c]);
      }
    }
  }
  return best;
}
const longestLine = solve;
class Solution { longestLine(mat) { return solve(mat); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestLine };
