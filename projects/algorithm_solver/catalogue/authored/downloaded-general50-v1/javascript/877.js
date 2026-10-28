'use strict';

// 877. Stone Game (Medium).
// Specification: https://leetcode.com/problems/stone-game/description/
function solve(piles) {
  const n = piles.length;
  const dp = Array.from({ length: n }, () => new Array(n).fill(0));
  for (let i = 0; i < n; i++) dp[i][i] = piles[i];
  for (let length = 2; length <= n; length++) {
    for (let i = 0; i + length - 1 < n; i++) {
      const j = i + length - 1;
      dp[i][j] = Math.max(piles[i] - dp[i + 1][j], piles[j] - dp[i][j - 1]);
    }
  }
  return dp[0][n - 1] > 0;
}
const stoneGame = solve;
class Solution { stoneGame(piles) { return solve(piles); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, stoneGame };
