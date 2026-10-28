'use strict';

// 223. Rectangle Area (Medium).
// Specification: https://leetcode.com/problems/rectangle-area/description/
function solve(ax1, ay1, ax2, ay2, bx1, by1, bx2, by2) {
  const areaA = (ax2 - ax1) * (ay2 - ay1);
  const areaB = (bx2 - bx1) * (by2 - by1);
  const overlapWidth = Math.max(0, Math.min(ax2, bx2) - Math.max(ax1, bx1));
  const overlapHeight = Math.max(0, Math.min(ay2, by2) - Math.max(ay1, by1));
  return areaA + areaB - overlapWidth * overlapHeight;
}
const computeArea = solve;
class Solution { computeArea(ax1, ay1, ax2, ay2, bx1, by1, bx2, by2) { return solve(ax1, ay1, ax2, ay2, bx1, by1, bx2, by2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, computeArea };
