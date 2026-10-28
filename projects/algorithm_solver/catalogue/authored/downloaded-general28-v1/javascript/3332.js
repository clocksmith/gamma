'use strict';

// 3332. Maximum Points Tourist Can Earn (Medium).
// Specification: https://leetcode.com/problems/maximum-points-tourist-can-earn/description/
function solve(n, k, stayScore, travelScore) {
  let dp = Array(n).fill(0);
  for (let day = 0; day < k; day++) {
    const ndp = Array(n).fill(-Infinity);
    for (let dest = 0; dest < n; dest++) {
      let best = dp[dest] + stayScore[day][dest];
      for (let curr = 0; curr < n; curr++) {
        if (curr !== dest) best = Math.max(best, dp[curr] + travelScore[curr][dest]);
      }
      ndp[dest] = best;
    }
    dp = ndp;
  }
  return Math.max(...dp);
}
const maxScore = solve;
class Solution { maxScore(n, k, stayScore, travelScore) { return solve(n, k, stayScore, travelScore); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxScore };
