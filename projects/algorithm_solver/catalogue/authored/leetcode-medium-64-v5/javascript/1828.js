'use strict';

// 1828. Queries on Number of Points Inside a Circle: compare squared distances without rounding or removing duplicate points.
// O(p * q) time and O(q) output space with O(1) auxiliary space; inputs are read-only.
function solve(points, queries) {
  const result = [];
  for (const [centerX, centerY, radius] of queries) {
    const squaredRadius = radius * radius;
    let count = 0;
    for (const [x, y] of points) {
      const dx = x - centerX;
      const dy = y - centerY;
      if (dx * dx + dy * dy <= squaredRadius) count += 1;
    }
    result.push(count);
  }
  return result;
}

const countPoints = solve;
class Solution {
  countPoints(points, queries) { return solve(points, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPoints };
