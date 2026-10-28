'use strict';

// 1037. Valid Boomerang (Easy).
// Specification: https://leetcode.com/problems/valid-boomerang/description/
function solve(points) {
  const [[x1, y1], [x2, y2], [x3, y3]] = points;
  if ((x1 === x2 && y1 === y2) || (x1 === x3 && y1 === y3) || (x2 === x3 && y2 === y3)) return false;
  return (x2 - x1) * (y3 - y1) !== (y2 - y1) * (x3 - x1);
}
const isBoomerang = solve;
class Solution { isBoomerang(points) { return solve(points); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isBoomerang };
