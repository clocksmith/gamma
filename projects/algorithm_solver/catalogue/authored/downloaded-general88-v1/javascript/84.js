'use strict';

// 84. Largest Rectangle in Histogram (Hard).
// Specification: https://leetcode.com/problems/largest-rectangle-in-histogram/description/
function solve(heights) {
  const stack = [];
  let best = 0;
  const extended = heights.concat([0]);
  for (let i = 0; i < extended.length; i++) {
    while (stack.length > 0 && extended[stack[stack.length - 1]] > extended[i]) {
      const height = extended[stack.pop()];
      const width = stack.length === 0 ? i : i - stack[stack.length - 1] - 1;
      best = Math.max(best, height * width);
    }
    stack.push(i);
  }
  return best;
}
const largestRectangleArea = solve;
class Solution { largestRectangleArea(heights) { return solve(heights); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestRectangleArea };
