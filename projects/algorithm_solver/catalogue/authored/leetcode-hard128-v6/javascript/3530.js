'use strict';

// 3530. Maximum Profit from Valid Topological Order in DAG.
// Subset dynamic programming appends only vertices whose predecessor masks are already selected; O(n*2^n) time and O(2^n+n) space. Inputs are preserved.

function solve(n, edges, score) {
  if (edges.length === 0) return score.slice().sort((a, b) => a - b).reduce((sum, value, index) => sum + (index + 1) * value, 0);
  const predecessors = new Int32Array(n);
  for (const [first, second] of edges) predecessors[second] |= 1 << first;
  const size = 1 << n, best = new Int32Array(size).fill(-1), population = new Uint8Array(size);
  best[0] = 0;
  for (let mask = 1; mask < size; mask += 1) population[mask] = population[mask >> 1] + (mask & 1);
  for (let mask = 0; mask < size; mask += 1) {
    if (best[mask] < 0) continue;
    const position = population[mask] + 1;
    let remaining = (size - 1) ^ mask;
    while (remaining) {
      const bit = remaining & -remaining, node = 31 - Math.clz32(bit);
      remaining ^= bit;
      if ((predecessors[node] & mask) === predecessors[node]) {
        const following = mask | bit;
        best[following] = Math.max(best[following], best[mask] + position * score[node]);
      }
    }
  }
  return best[size - 1];
}

const maxProfit = solve;
class Solution {
  maxProfit(n, edges, score) { return solve(n, edges, score); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProfit };
