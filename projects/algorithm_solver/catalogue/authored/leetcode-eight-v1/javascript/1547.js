'use strict';

// O(m^3) time, O(m^2) space. Sorting is confined to a new array.
function solve(n, cuts) {
  const positions = [0, ...cuts.slice().sort((a, b) => a - b), n];
  const size = positions.length;
  const cost = Array.from({ length: size }, () => Array(size).fill(0));
  for (let width = 2; width < size; width += 1) {
    for (let left = 0; left + width < size; left += 1) {
      const right = left + width;
      let best = Infinity;
      for (let cut = left + 1; cut < right; cut += 1) {
        best = Math.min(best, cost[left][cut] + cost[cut][right]);
      }
      cost[left][right] = positions[right] - positions[left] + best;
    }
  }
  return cost[0][size - 1];
}

const minCost = solve;
class Solution {
  minCost(n, cuts) { return solve(n, cuts); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCost };
