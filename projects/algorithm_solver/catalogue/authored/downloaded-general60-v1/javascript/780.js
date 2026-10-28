'use strict';

// 780. Reaching Points (Hard).
// Specification: https://leetcode.com/problems/reaching-points/description/
function solve(sx, sy, tx, ty) {
  let x = tx; let y = ty;
  while (x >= sx && y >= sy) {
    if (x === sx && y === sy) return true;
    if (x === y) return false;
    if (x > y) {
      if (y > sy) x %= y;
      else return (x - sx) % y === 0;
    } else {
      if (x > sx) y %= x;
      else return (y - sy) % x === 0;
    }
  }
  return false;
}
const reachingPoints = solve;
class Solution { reachingPoints(sx, sy, tx, ty) { return solve(sx, sy, tx, ty); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reachingPoints };
