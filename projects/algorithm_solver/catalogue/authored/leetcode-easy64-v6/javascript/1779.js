'use strict';

// 1779. Find Nearest Point That Has the Same X or Y Coordinate (Easy).
// Specification: https://leetcode.com/problems/find-nearest-point-that-has-the-same-x-or-y-coordinate/description/
// O(n) time, O(1) space; equal distances keep the first index; preserve points.
function solve(x, y, points) {
  let bestIndex = -1;
  let bestDistance = Infinity;
  for (let index = 0; index < points.length; index++) {
    const [pointX, pointY] = points[index];
    if (pointX !== x && pointY !== y) continue;
    const distance = Math.abs(pointX - x) + Math.abs(pointY - y);
    if (distance < bestDistance) {
      bestIndex = index;
      bestDistance = distance;
    }
  }
  return bestIndex;
}

const nearestValidPoint = solve;
class Solution {
  nearestValidPoint(x, y, points) { return solve(x, y, points); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, nearestValidPoint };
