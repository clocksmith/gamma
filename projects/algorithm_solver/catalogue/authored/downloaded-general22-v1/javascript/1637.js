'use strict';

// 1637. Widest Vertical Area Between Two Points Containing No Points (Medium).
// Specification: https://leetcode.com/problems/widest-vertical-area-between-two-points-containing-no-points/description/
function solve(points) {
  const xs = points.map(([x]) => x).sort((a, b) => a - b);
  let best = 0;
  for (let i = 1; i < xs.length; i++) best = Math.max(best, xs[i] - xs[i - 1]);
  return best;
}
const maxWidthOfVerticalArea = solve;
class Solution { maxWidthOfVerticalArea(points) { return solve(points); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxWidthOfVerticalArea };
