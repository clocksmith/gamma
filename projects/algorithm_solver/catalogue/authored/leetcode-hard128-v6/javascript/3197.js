'use strict';

// 3197. Find the Minimum Area to Cover All Ones II.
// Enumerate the six possible three-rectangle split layouts; O(h*w*(h^2+w^2+h*w)) time, O(1) auxiliary space. Inputs are preserved.

function solve(grid) {
  const h = grid.length, w = grid[0].length;
  function area(top, bottom, left, right) {
    let minRow = h, maxRow = -1, minCol = w, maxCol = -1;
    for (let row = top; row < bottom; row += 1) {
      for (let col = left; col < right; col += 1) {
        if (grid[row][col]) { minRow = Math.min(minRow, row); maxRow = Math.max(maxRow, row); minCol = Math.min(minCol, col); maxCol = Math.max(maxCol, col); }
      }
    }
    return maxRow < 0 ? Infinity : (maxRow - minRow + 1) * (maxCol - minCol + 1);
  }
  let answer = Infinity;
  for (let first = 1; first < h; first += 1) for (let second = first + 1; second < h; second += 1) answer = Math.min(answer, area(0, first, 0, w) + area(first, second, 0, w) + area(second, h, 0, w));
  for (let first = 1; first < w; first += 1) for (let second = first + 1; second < w; second += 1) answer = Math.min(answer, area(0, h, 0, first) + area(0, h, first, second) + area(0, h, second, w));
  for (let row = 1; row < h; row += 1) {
    for (let col = 1; col < w; col += 1) {
      answer = Math.min(answer,
        area(0, row, 0, w) + area(row, h, 0, col) + area(row, h, col, w),
        area(row, h, 0, w) + area(0, row, 0, col) + area(0, row, col, w),
        area(0, h, 0, col) + area(0, row, col, w) + area(row, h, col, w),
        area(0, h, col, w) + area(0, row, 0, col) + area(row, h, 0, col));
    }
  }
  return answer;
}

const minimumSum = solve;
class Solution {
  minimumSum(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumSum };
