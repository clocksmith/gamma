'use strict';

// 812. Largest Triangle Area (Easy).
// Specification: https://leetcode.com/problems/largest-triangle-area/description/
// O(n^3) time, O(1) auxiliary space; maximize the absolute integer cross product.
function solve(points) {
  let largestDoubleArea = 0;
  for (let first = 0; first < points.length - 2; first++) {
    for (let second = first + 1; second < points.length - 1; second++) {
      for (let third = second + 1; third < points.length; third++) {
        const [ax, ay] = points[first];
        const [bx, by] = points[second];
        const [cx, cy] = points[third];
        const doubleArea = Math.abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax));
        largestDoubleArea = Math.max(largestDoubleArea, doubleArea);
      }
    }
  }
  return largestDoubleArea / 2;
}

const largestTriangleArea = solve;
class Solution {
  largestTriangleArea(points) { return solve(points); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestTriangleArea };
