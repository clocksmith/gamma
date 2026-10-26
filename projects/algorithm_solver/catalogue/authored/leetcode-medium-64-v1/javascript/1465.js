'use strict';

// 1465. Maximum Area of a Piece of Cake After Horizontal and Vertical Cuts: multiply the largest gaps including both cake boundaries.
// O(a log a + b log b) time and O(a + b) space for a horizontal and b vertical cuts; inputs are read-only.
function solve(h, w, horizontalCuts, verticalCuts) {
  function largestGap(length, cuts) {
    let previous = 0;
    let best = 0;
    for (const cut of [...cuts].sort((left, right) => left - right)) {
      best = Math.max(best, cut - previous);
      previous = cut;
    }
    return Math.max(best, length - previous);
  }
  const height = largestGap(h, horizontalCuts);
  const width = largestGap(w, verticalCuts);
  // The area can exceed Number's exact integer range before reduction.
  return Number(BigInt(height) * BigInt(width) % 1000000007n);
}

const maxArea = solve;
class Solution {
  maxArea(h, w, horizontalCuts, verticalCuts) { return solve(h, w, horizontalCuts, verticalCuts); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxArea };
