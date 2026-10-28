'use strict';

// 939. Minimum Area Rectangle (Medium).
// Specification: https://leetcode.com/problems/minimum-area-rectangle/description/
function solve(points) {
  const pointSet = new Set(points.map(([x, y]) => x + ',' + y));
  let best = Infinity;
  for (let i = 0; i < points.length; i++) {
    for (let j = i + 1; j < points.length; j++) {
      const [x1, y1] = points[i]; const [x2, y2] = points[j];
      if (x1 === x2 || y1 === y2) continue;
      if (pointSet.has(x1 + ',' + y2) && pointSet.has(x2 + ',' + y1)) best = Math.min(best, Math.abs(x2 - x1) * Math.abs(y2 - y1));
    }
  }
  return best === Infinity ? 0 : best;
}
const minAreaRect = solve;
class Solution { minAreaRect(points) { return solve(points); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minAreaRect };
