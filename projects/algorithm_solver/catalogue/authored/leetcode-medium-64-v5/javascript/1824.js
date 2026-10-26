'use strict';

// 1824. Minimum Sideway Jumps: carry the cheapest reachable cost for each of the three lanes.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(obstacles) {
  const unreachable = obstacles.length + 1;
  const costs = [1, 0, 1];
  for (const obstacle of obstacles) {
    if (obstacle !== 0) costs[obstacle - 1] = unreachable;
    const best = Math.min(costs[0], costs[1], costs[2]);
    for (let lane = 0; lane < 3; lane += 1) {
      if (lane + 1 !== obstacle) costs[lane] = Math.min(costs[lane], best + 1);
    }
  }
  return Math.min(costs[0], costs[1], costs[2]);
}

const minSideJumps = solve;
class Solution {
  minSideJumps(obstacles) { return solve(obstacles); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSideJumps };
