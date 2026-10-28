'use strict';

// 1626. Best Team With No Conflicts (Medium).
// Specification: https://leetcode.com/problems/best-team-with-no-conflicts/description/
function solve(scores, ages) {
  const players = scores.map((score, i) => [ages[i], score]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const dp = new Array(players.length).fill(0);
  let best = 0;
  for (let i = 0; i < players.length; i++) {
    dp[i] = players[i][1];
    for (let j = 0; j < i; j++) { if (players[j][1] <= players[i][1]) dp[i] = Math.max(dp[i], dp[j] + players[i][1]); }
    best = Math.max(best, dp[i]);
  }
  return best;
}
const bestTeamScore = solve;
class Solution { bestTeamScore(scores, ages) { return solve(scores, ages); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, bestTeamScore };
