'use strict';

// 1615. Maximal Network Rank: combine endpoint degrees and subtract their shared road once.
// O(n^2 + e) expected time and O(n + e) auxiliary space; inputs are read-only.
function solve(n, roads) {
  const neighbors = Array.from({ length: n }, () => new Set());
  for (const [first, second] of roads) {
    neighbors[first].add(second);
    neighbors[second].add(first);
  }
  let best = 0;
  for (let first = 0; first < n; first += 1) {
    for (let second = first + 1; second < n; second += 1) {
      const rank = neighbors[first].size + neighbors[second].size - (neighbors[first].has(second) ? 1 : 0);
      best = Math.max(best, rank);
    }
  }
  return best;
}

const maximalNetworkRank = solve;
class Solution {
  maximalNetworkRank(n, roads) { return solve(n, roads); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximalNetworkRank };
