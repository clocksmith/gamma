'use strict';

// 1292. Maximum Side Length of a Square with Sum Less than or Equal to Threshold (Medium).
// Specification: https://leetcode.com/problems/maximum-side-length-of-a-square-with-sum-less-than-or-equal-to-threshold/description/
function solve(mat, threshold) {
  const rows = mat.length; const cols = mat[0].length;
  const prefix = Array.from({ length: rows + 1 }, () => new Array(cols + 1).fill(0));
  for (let r = 0; r < rows; r++) { for (let c = 0; c < cols; c++) prefix[r + 1][c + 1] = mat[r][c] + prefix[r][c + 1] + prefix[r + 1][c] - prefix[r][c]; }
  function squareSum(r, c, side) { return prefix[r + side][c + side] - prefix[r][c + side] - prefix[r + side][c] + prefix[r][c]; }
  let best = 0;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      let left = best + 1; let right = Math.min(rows - r, cols - c); let found = best;
      while (left <= right) {
        const mid = Math.floor((left + right) / 2);
        if (squareSum(r, c, mid) <= threshold) { found = mid; left = mid + 1; } else right = mid - 1;
      }
      best = Math.max(best, found);
    }
  }
  return best;
}
const maxSideLength = solve;
class Solution { maxSideLength(mat, threshold) { return solve(mat, threshold); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSideLength };
