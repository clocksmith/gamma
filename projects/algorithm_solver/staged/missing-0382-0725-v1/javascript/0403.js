'use strict';

// 403. Frog Jump. Propagate feasible previous jump lengths to later stones.

function solve(stones) {
  const jumps = new Map(stones.map(position => [position, new Set()]));
  jumps.get(0).add(0);
  for (const position of stones) {
    for (const jump of jumps.get(position)) {
      for (let step = jump - 1; step <= jump + 1; step += 1) {
        if (step > 0 && jumps.has(position + step)) jumps.get(position + step).add(step);
      }
    }
  }
  return jumps.get(stones[stones.length - 1]).size > 0;
}

const canCross = solve;
class Solution {
  canCross(stones) { return solve(stones); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canCross };
