'use strict';

// 661. Image Smoother (Easy).
// Specification: https://leetcode.com/problems/image-smoother/description/
// O(m * n) time and space; floor each neighborhood average into a fresh matrix.
function solve(img) {
  const rows = img.length;
  const columns = img[0].length;
  const result = Array.from({ length: rows }, () => new Array(columns).fill(0));
  for (let row = 0; row < rows; row++) {
    for (let column = 0; column < columns; column++) {
      let total = 0;
      let count = 0;
      for (let nearRow = Math.max(0, row - 1); nearRow <= Math.min(rows - 1, row + 1); nearRow++) {
        for (let nearColumn = Math.max(0, column - 1); nearColumn <= Math.min(columns - 1, column + 1); nearColumn++) {
          total += img[nearRow][nearColumn];
          count++;
        }
      }
      result[row][column] = Math.floor(total / count);
    }
  }
  return result;
}

const imageSmoother = solve;
class Solution {
  imageSmoother(img) { return solve(img); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, imageSmoother };
