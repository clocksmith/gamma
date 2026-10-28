'use strict';

// 475. Heaters (Medium).
// Specification: https://leetcode.com/problems/heaters/description/
function solve(houses, heaters) {
  const sortedHeaters = heaters.slice().sort((a, b) => a - b);
  let radius = 0;
  for (const house of houses) {
    let left = 0; let right = sortedHeaters.length - 1; let best = Infinity;
    while (left <= right) {
      const mid = Math.floor((left + right) / 2);
      best = Math.min(best, Math.abs(sortedHeaters[mid] - house));
      if (sortedHeaters[mid] < house) left = mid + 1; else right = mid - 1;
    }
    radius = Math.max(radius, best);
  }
  return radius;
}
const findRadius = solve;
class Solution { findRadius(houses, heaters) { return solve(houses, heaters); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findRadius };
