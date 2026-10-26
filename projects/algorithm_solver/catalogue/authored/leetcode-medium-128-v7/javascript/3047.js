'use strict';

// 3047. Find the Largest Area of Square Inside Two Rectangles: inspect each rectangle intersection and take its smaller positive dimension.
// O(n * n) time and O(1) auxiliary space; inputs are read-only.
function solve(bottomLeft, topRight) {
  let best = 0;
  for (let left = 0; left < bottomLeft.length; left += 1) {
    for (let right = left + 1; right < bottomLeft.length; right += 1) {
      const width = Math.min(topRight[left][0], topRight[right][0]) - Math.max(bottomLeft[left][0], bottomLeft[right][0]);
      const height = Math.min(topRight[left][1], topRight[right][1]) - Math.max(bottomLeft[left][1], bottomLeft[right][1]);
      const side = Math.min(width, height);
      if (side > 0) best = Math.max(best, side * side);
    }
  }
  return best;
}

const largestSquareArea = solve;
class Solution {
  largestSquareArea(bottomLeft, topRight) { return solve(bottomLeft, topRight); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestSquareArea };
