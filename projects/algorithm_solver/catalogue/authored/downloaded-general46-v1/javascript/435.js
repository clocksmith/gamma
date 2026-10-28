'use strict';

// 435. Non-overlapping Intervals (Medium).
// Specification: https://leetcode.com/problems/non-overlapping-intervals/description/
function solve(intervals) {
  if (intervals.length === 0) return 0;
  const sorted = intervals.slice().sort((a, b) => a[1] - b[1]);
  let kept = 1; let end = sorted[0][1];
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i][0] >= end) { kept++; end = sorted[i][1]; }
  }
  return intervals.length - kept;
}
const eraseOverlapIntervals = solve;
class Solution { eraseOverlapIntervals(intervals) { return solve(intervals); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, eraseOverlapIntervals };
