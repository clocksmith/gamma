'use strict';

// 221. Maximal Square (Medium).
// Specification: https://leetcode.com/problems/maximal-square/description/
function solve(matrix) {
  if (matrix.length === 0) return 0;
  const rows = matrix.length; const cols = matrix[0].length;
  const dp = Array.from({ length: rows + 1 }, () => new Array(cols + 1).fill(0));
  let best = 0;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (matrix[r][c] === '1') {
        dp[r + 1][c + 1] = 1 + Math.min(dp[r][c], dp[r + 1][c], dp[r][c + 1]);
        best = Math.max(best, dp[r + 1][c + 1]);
      }
    }
  }
  return best * best;
}
const maximalSquare = solve;
class Solution { maximalSquare(matrix) { return solve(matrix); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximalSquare };
