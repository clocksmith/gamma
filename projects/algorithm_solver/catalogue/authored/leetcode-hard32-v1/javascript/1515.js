'use strict';

// 1515. Best Position for a Service Centre.
// Nested convex ternary search: O(n*I^2) time, O(1) workspace, I=80.
// This problem requires an approximate floating-point minimum, not an exact rational.
function solve(positions) {
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  for (const [x, y] of positions) {
    minX = Math.min(minX, x);
    maxX = Math.max(maxX, x);
    minY = Math.min(minY, y);
    maxY = Math.max(maxY, y);
  }
  function distance(x, y) {
    let total = 0;
    for (const [px, py] of positions) total += Math.hypot(x - px, y - py);
    return total;
  }
  function bestAtX(x) {
    let low = minY;
    let high = maxY;
    for (let iteration = 0; iteration < 80; iteration += 1) {
      const left = low + (high - low) / 3;
      const right = high - (high - low) / 3;
      if (distance(x, left) <= distance(x, right)) high = right;
      else low = left;
    }
    return distance(x, (low + high) / 2);
  }
  let low = minX;
  let high = maxX;
  for (let iteration = 0; iteration < 80; iteration += 1) {
    const left = low + (high - low) / 3;
    const right = high - (high - low) / 3;
    if (bestAtX(left) <= bestAtX(right)) high = right;
    else low = left;
  }
  return bestAtX((low + high) / 2);
}

const getMinDistSum = solve;
class Solution {
  getMinDistSum(positions) { return solve(positions); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getMinDistSum };
