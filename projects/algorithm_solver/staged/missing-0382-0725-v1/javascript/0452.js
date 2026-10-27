'use strict';

// 452. Minimum Number of Arrows to Burst Balloons.

function solve(points) {
  let end = null, arrows = 0;
  for (const [left, right] of points.slice().sort((a, b) => a[1] - b[1])) {
    if (end === null || left > end) { end = right; arrows += 1; }
  }
  return arrows;
}

const findMinArrowShots = solve;
class Solution {
  findMinArrowShots(points) { return solve(points); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMinArrowShots };
