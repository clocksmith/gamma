/**
 * 84. Largest Rectangle in Histogram (Hard).
 * Fresh candidate authored in this conversation; no repository solution copied.
 * Specification: https://leetcode.com/problems/largest-rectangle-in-histogram/description/
 * Canonical API: solve(heights); native alias: largestRectangleArea(heights).
 * Inputs are preserved. Gamma independent qualification is pending.
 */
'use strict';

function solve(heights) {
  const stack = [];
  let largestArea = 0;
  for (let right = 0; right <= heights.length; right++) {
    const currentHeight = right < heights.length ? heights[right] : 0;
    while (stack.length > 0 && heights[stack[stack.length - 1]] > currentHeight) {
      const rectangleHeight = heights[stack.pop()];
      const left = stack.length > 0 ? stack[stack.length - 1] + 1 : 0;
      largestArea = Math.max(largestArea, rectangleHeight * (right - left));
    }
    if (right < heights.length) {
      stack.push(right);
    }
  }
  return largestArea;
}

function largestRectangleArea(heights) {
  return solve(heights);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, largestRectangleArea };
}
