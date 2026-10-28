'use strict';

// 3030. Find the Grid of Region Average (Medium).
// Specification: https://leetcode.com/problems/find-the-grid-of-region-average/description/
function isRegion(image, i, j, threshold) {
  for (let x = i; x < i + 3; x++) {
    for (let y = j; y < j + 3; y++) {
      if (x > i && Math.abs(image[x][y] - image[x - 1][y]) > threshold) return false;
      if (y > j && Math.abs(image[x][y] - image[x][y - 1]) > threshold) return false;
    }
  }
  return true;
}
function solve(image, threshold) {
  const m = image.length; const n = image[0].length;
  const sums = Array.from({ length: m }, () => Array(n).fill(0));
  const counts = Array.from({ length: m }, () => Array(n).fill(0));
  for (let i = 0; i + 2 < m; i++) {
    for (let j = 0; j + 2 < n; j++) {
      if (!isRegion(image, i, j, threshold)) continue;
      let total = 0;
      for (let x = i; x < i + 3; x++) for (let y = j; y < j + 3; y++) total += image[x][y];
      const average = Math.floor(total / 9);
      for (let x = i; x < i + 3; x++) {
        for (let y = j; y < j + 3; y++) { sums[x][y] += average; counts[x][y]++; }
      }
    }
  }
  const result = image.map((row) => row.slice());
  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      if (counts[i][j] > 0) result[i][j] = Math.floor(sums[i][j] / counts[i][j]);
    }
  }
  return result;
}
const resultGrid = solve;
class Solution { resultGrid(image, threshold) { return solve(image, threshold); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, resultGrid };
