'use strict';

// 688. Knight Probability in Chessboard (Medium).
// Specification: https://leetcode.com/problems/knight-probability-in-chessboard/description/
function solve(n, k, row, column) {
  let dp = Array.from({ length: n }, () => new Array(n).fill(0));
  dp[row][column] = 1;
  const moves = [[-2, -1], [-2, 1], [-1, -2], [-1, 2], [1, -2], [1, 2], [2, -1], [2, 1]];
  for (let step = 0; step < k; step++) {
    const next = Array.from({ length: n }, () => new Array(n).fill(0));
    for (let r = 0; r < n; r++) {
      for (let c = 0; c < n; c++) {
        if (dp[r][c] === 0) continue;
        for (const [dr, dc] of moves) {
          const nr = r + dr; const nc = c + dc;
          if (nr >= 0 && nr < n && nc >= 0 && nc < n) next[nr][nc] += dp[r][c] / 8;
        }
      }
    }
    dp = next;
  }
  let total = 0;
  for (const rowValues of dp) { for (const value of rowValues) total += value; }
  return total;
}
const knightProbability = solve;
class Solution { knightProbability(n, k, row, column) { return solve(n, k, row, column); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, knightProbability };
