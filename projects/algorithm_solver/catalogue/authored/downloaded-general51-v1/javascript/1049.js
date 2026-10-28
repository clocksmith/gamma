'use strict';

// 1049. Last Stone Weight II (Medium).
// Specification: https://leetcode.com/problems/last-stone-weight-ii/description/
function solve(stones) {
  const total = stones.reduce((sum, value) => sum + value, 0);
  const reachable = new Set([0]);
  for (const stone of stones) {
    const next = new Set(reachable);
    for (const value of reachable) next.add(value + stone);
    for (const value of next) reachable.add(value);
  }
  let best = 0;
  for (const value of reachable) { if (value <= Math.floor(total / 2)) best = Math.max(best, value); }
  return total - 2 * best;
}
const lastStoneWeightII = solve;
class Solution { lastStoneWeightII(stones) { return solve(stones); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, lastStoneWeightII };
