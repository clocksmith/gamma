'use strict';

// 403. Frog Jump (Hard).
// Specification: https://leetcode.com/problems/frog-jump/description/
function solve(stones) {
  const positions = new Set(stones);
  const reachable = new Map();
  for (const stone of stones) reachable.set(stone, new Set());
  reachable.get(stones[0]).add(0);
  for (const stone of stones) {
    for (const jump of reachable.get(stone)) {
      for (const nextJump of [jump - 1, jump, jump + 1]) {
        if (nextJump > 0 && positions.has(stone + nextJump)) reachable.get(stone + nextJump).add(nextJump);
      }
    }
  }
  return reachable.get(stones[stones.length - 1]).size > 0;
}
const canCross = solve;
class Solution { canCross(stones) { return solve(stones); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, canCross };
