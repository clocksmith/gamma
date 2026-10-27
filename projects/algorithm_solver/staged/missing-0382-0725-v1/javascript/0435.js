'use strict';

// 435. Non-overlapping Intervals. Greedily retain earliest-finishing intervals; input is preserved.

function solve(intervals) {
  let end = -Infinity, removed = 0;
  for (const [left, right] of intervals.slice().sort((a, b) => a[1] - b[1])) {
    if (left < end) removed += 1;
    else end = right;
  }
  return removed;
}

const eraseOverlapIntervals = solve;
class Solution {
  eraseOverlapIntervals(intervals) { return solve(intervals); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, eraseOverlapIntervals };
