'use strict';

// 452. Minimum Number of Arrows to Burst Balloons (Medium).
// Specification: https://leetcode.com/problems/minimum-number-of-arrows-to-burst-balloons/description/
function solve(points) {
  if (points.length === 0) return 0;
  const sorted = points.slice().sort((a, b) => a[1] - b[1]);
  let arrows = 1; let end = sorted[0][1];
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i][0] > end) { arrows++; end = sorted[i][1]; }
  }
  return arrows;
}
const findMinArrowShots = solve;
class Solution { findMinArrowShots(points) { return solve(points); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMinArrowShots };
