'use strict';

// 1620. Coordinate With Maximum Network Quality (Medium).
// Specification: https://leetcode.com/problems/coordinate-with-maximum-network-quality/description/
function solve(towers, radius) {
  let bestQuality = -1; let bestX = 0; let bestY = 0;
  for (let x = 0; x <= 50; x++) {
    for (let y = 0; y <= 50; y++) {
      let quality = 0;
      for (const [tx, ty, q] of towers) {
        const distance = Math.sqrt((x - tx) * (x - tx) + (y - ty) * (y - ty));
        if (distance <= radius) quality += Math.floor(q / (1 + distance));
      }
      if (quality > bestQuality) { bestQuality = quality; bestX = x; bestY = y; }
    }
  }
  return [bestX, bestY];
}
const bestCoordinate = solve;
class Solution { bestCoordinate(towers, radius) { return solve(towers, radius); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, bestCoordinate };
