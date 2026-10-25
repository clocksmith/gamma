/**
 * 85. Maximal Rectangle (Hard).
 * Fresh candidate authored in this conversation; no repository solution copied.
 * Specification: https://leetcode.com/problems/maximal-rectangle/description/
 * Canonical API: solve(matrix); native alias: maximalRectangle(matrix).
 * Inputs are preserved. Gamma independent qualification is pending.
 */
'use strict';

function solve(matrix) {
  if (matrix.length === 0 || matrix[0].length === 0) {
    return 0;
  }
  const columns = matrix[0].length;
  const heights = new Array(columns).fill(0);
  let largestArea = 0;
  for (const row of matrix) {
    for (let column = 0; column < columns; column++) {
      heights[column] = row[column] === '1' ? heights[column] + 1 : 0;
    }
    const stack = [];
    for (let right = 0; right <= columns; right++) {
      const currentHeight = right < columns ? heights[right] : 0;
      while (stack.length > 0 && heights[stack[stack.length - 1]] > currentHeight) {
        const rectangleHeight = heights[stack.pop()];
        const left = stack.length > 0 ? stack[stack.length - 1] + 1 : 0;
        largestArea = Math.max(largestArea, rectangleHeight * (right - left));
      }
      if (right < columns) {
        stack.push(right);
      }
    }
  }
  return largestArea;
}

function maximalRectangle(matrix) {
  return solve(matrix);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, maximalRectangle };
}
