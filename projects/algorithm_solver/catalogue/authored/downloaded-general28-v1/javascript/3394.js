'use strict';

// 3394. Check if Grid can be Cut into Sections (Medium).
// Specification: https://leetcode.com/problems/check-if-grid-can-be-cut-into-sections/description/
function solve(n, rectangles) {
  function groups(intervals) {
    intervals.sort((a, b) => a[0] - b[0]);
    let count = 0; let curEnd = -Infinity;
    for (const [s, e] of intervals) {
      if (s >= curEnd) { count++; curEnd = e; }
      else if (e > curEnd) curEnd = e;
    }
    return count;
  }
  const xs = rectangles.map((r) => [r[0], r[2]]);
  const ys = rectangles.map((r) => [r[1], r[3]]);
  return groups(xs) >= 3 || groups(ys) >= 3;
}
const checkIfGridCanBeCutIntoSections = solve;
class Solution { checkIfGridCanBeCutIntoSections(n, rectangles) { return solve(n, rectangles); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkIfGridCanBeCutIntoSections };
