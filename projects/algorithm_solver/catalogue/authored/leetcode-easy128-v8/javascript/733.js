'use strict';

// 733. Flood Fill (Easy).
// Specification: https://leetcode.com/problems/flood-fill/description/
// O(m * n) time and space; iterative traversal colors a fresh image and preserves input rows.
function solve(image, sr, sc, color) {
  const result = image.map(row => row.slice());
  const original = image[sr][sc];
  if (original === color) return result;
  const stack = [[sr, sc]];
  result[sr][sc] = color;
  const directions = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  while (stack.length > 0) {
    const [row, column] = stack.pop();
    for (const [rowStep, columnStep] of directions) {
      const nextRow = row + rowStep;
      const nextColumn = column + columnStep;
      if (nextRow >= 0 && nextRow < result.length && nextColumn >= 0 && nextColumn < result[0].length && result[nextRow][nextColumn] === original) {
        result[nextRow][nextColumn] = color;
        stack.push([nextRow, nextColumn]);
      }
    }
  }
  return result;
}

const floodFill = solve;
class Solution {
  floodFill(image, sr, sc, color) { return solve(image, sr, sc, color); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, floodFill };
