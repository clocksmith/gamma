'use strict';

// 1014. Best Sightseeing Pair (Medium).
// Specification: https://leetcode.com/problems/best-sightseeing-pair/description/
function solve(values) {
  let best = 0; let bestLeft = values[0] + 0;
  for (let j = 1; j < values.length; j++) {
    best = Math.max(best, bestLeft + values[j] - j);
    bestLeft = Math.max(bestLeft, values[j] + j);
  }
  return best;
}
const maxScoreSightseeingPair = solve;
class Solution { maxScoreSightseeingPair(values) { return solve(values); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxScoreSightseeingPair };
