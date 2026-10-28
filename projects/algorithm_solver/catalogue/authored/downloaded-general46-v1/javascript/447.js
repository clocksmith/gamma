'use strict';

// 447. Number of Boomerangs (Medium).
// Specification: https://leetcode.com/problems/number-of-boomerangs/description/
function solve(points) {
  let total = 0;
  for (const [x1, y1] of points) {
    const counts = {};
    for (const [x2, y2] of points) {
      const distance = (x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2);
      counts[distance] = (counts[distance] || 0) + 1;
    }
    for (const count of Object.values(counts)) total += count * (count - 1);
  }
  return total;
}
const numberOfBoomerangs = solve;
class Solution { numberOfBoomerangs(points) { return solve(points); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfBoomerangs };
