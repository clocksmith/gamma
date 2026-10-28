'use strict';

// 174. Dungeon Game (Hard).
// Specification: https://leetcode.com/problems/dungeon-game/description/
function solve(dungeon) {
  const rows = dungeon.length; const cols = dungeon[0].length;
  const dp = Array.from({ length: rows }, () => new Array(cols).fill(0));
  for (let r = rows - 1; r >= 0; r--) {
    for (let c = cols - 1; c >= 0; c--) {
      if (r === rows - 1 && c === cols - 1) dp[r][c] = Math.max(1, 1 - dungeon[r][c]);
      else if (r === rows - 1) dp[r][c] = Math.max(1, dp[r][c + 1] - dungeon[r][c]);
      else if (c === cols - 1) dp[r][c] = Math.max(1, dp[r + 1][c] - dungeon[r][c]);
      else dp[r][c] = Math.max(1, Math.min(dp[r + 1][c], dp[r][c + 1]) - dungeon[r][c]);
    }
  }
  return dp[0][0];
}
const calculateMinimumHP = solve;
class Solution { calculateMinimumHP(dungeon) { return solve(dungeon); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, calculateMinimumHP };
