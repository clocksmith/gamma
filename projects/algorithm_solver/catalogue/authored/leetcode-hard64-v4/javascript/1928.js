'use strict';

// 1928. Minimum Cost to Reach Destination in Time. Exact-time dynamic programming on positive-duration edges; O(T*(V+E)) time and O(T*V) space. Inputs are preserved.

function solve(maxTime, edges, passingFees) {
  const size = passingFees.length;
  const best = Array.from({ length: maxTime + 1 }, () => new Float64Array(size).fill(Infinity));
  best[0][0] = passingFees[0];
  for (let elapsed = 1; elapsed <= maxTime; elapsed += 1) {
    const current = best[elapsed];
    for (const [first, second, duration] of edges) {
      if (duration <= elapsed) {
        const previous = best[elapsed - duration];
        current[first] = Math.min(current[first], previous[second] + passingFees[first]);
        current[second] = Math.min(current[second], previous[first] + passingFees[second]);
      }
    }
  }
  let answer = Infinity;
  for (const row of best) answer = Math.min(answer, row[size - 1]);
  return answer === Infinity ? -1 : answer;
}

const minCost = solve;
class Solution {
  minCost(maxTime, edges, passingFees) { return solve(maxTime, edges, passingFees); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCost };
