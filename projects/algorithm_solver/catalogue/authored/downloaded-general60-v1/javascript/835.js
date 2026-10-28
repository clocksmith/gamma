'use strict';

// 835. Image Overlap (Medium).
// Specification: https://leetcode.com/problems/image-overlap/description/
function solve(img1, img2) {
  const n = img1.length;
  const ones1 = [];
  const ones2 = [];
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      if (img1[r][c] === 1) ones1.push([r, c]);
      if (img2[r][c] === 1) ones2.push([r, c]);
    }
  }
  const counts = {};
  let best = 0;
  for (const [r1, c1] of ones1) {
    for (const [r2, c2] of ones2) {
      const key = (r1 - r2) + ',' + (c1 - c2);
      counts[key] = (counts[key] || 0) + 1;
      best = Math.max(best, counts[key]);
    }
  }
  return best;
}
const largestOverlap = solve;
class Solution { largestOverlap(img1, img2) { return solve(img1, img2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestOverlap };
