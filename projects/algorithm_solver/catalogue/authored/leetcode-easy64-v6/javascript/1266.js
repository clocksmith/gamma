'use strict';

// 1266. Minimum Time Visiting All Points (Easy).
// Specification: https://leetcode.com/problems/minimum-time-visiting-all-points/description/
// O(n) time, O(1) space; preserve points and their order.
function solve(points) {
  let result = 0;
  for (let index = 1; index < points.length; index++) {
    const deltaX = Math.abs(points[index][0] - points[index - 1][0]);
    const deltaY = Math.abs(points[index][1] - points[index - 1][1]);
    result += Math.max(deltaX, deltaY);
  }
  return result;
}

const minTimeToVisitAllPoints = solve;
class Solution {
  minTimeToVisitAllPoints(points) { return solve(points); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minTimeToVisitAllPoints };
