'use strict';

// 836. Rectangle Overlap (Easy).
// Specification: https://leetcode.com/problems/rectangle-overlap/description/
// O(1) time and space; shared edges or corners do not count as positive-area overlap.
function solve(rec1, rec2) {
  return Math.max(rec1[0], rec2[0]) < Math.min(rec1[2], rec2[2]) &&
    Math.max(rec1[1], rec2[1]) < Math.min(rec1[3], rec2[3]);
}

const isRectangleOverlap = solve;
class Solution {
  isRectangleOverlap(rec1, rec2) { return solve(rec1, rec2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isRectangleOverlap };
