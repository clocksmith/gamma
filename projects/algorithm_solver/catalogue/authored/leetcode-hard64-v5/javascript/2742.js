'use strict';

// 2742. Painting the Walls. Zero-one knapsack on the number of walls covered by a paid job; O(n^2) time and O(n) space. Inputs are preserved.

function solve(cost, time) {
  const size = cost.length;
  const best = Array(size + 1).fill(Infinity);
  best[0] = 0;
  for (let index = 0; index < size; index += 1) {
    for (let covered = size - 1; covered >= 0; covered -= 1) {
      const following = Math.min(size, covered + time[index] + 1);
      best[following] = Math.min(best[following], best[covered] + cost[index]);
    }
  }
  return best[size];
}

const paintWalls = solve;
class Solution {
  paintWalls(cost, time) { return solve(cost, time); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, paintWalls };
