'use strict';

// 1401. Circle and Rectangle Overlapping: compare the nearest rectangle point with the squared radius.
// O(1) time and O(1) auxiliary space; inputs are read-only.
function solve(radius, xCenter, yCenter, x1, y1, x2, y2) {
  const nearestX = Math.min(Math.max(xCenter, x1), x2);
  const nearestY = Math.min(Math.max(yCenter, y1), y2);
  const dx = xCenter - nearestX;
  const dy = yCenter - nearestY;
  return dx * dx + dy * dy <= radius * radius;
}

const checkOverlap = solve;
class Solution {
  checkOverlap(radius, xCenter, yCenter, x1, y1, x2, y2) { return solve(radius, xCenter, yCenter, x1, y1, x2, y2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkOverlap };
