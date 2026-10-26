'use strict';

// 1288. Remove Covered Intervals: sort starts increasingly and equal-start ends decreasingly.
// O(n log(n + 1)) time and O(n) auxiliary space; inputs are read-only.
function solve(intervals) {
  const ordered = intervals.slice().sort((a, b) => a[0] - b[0] || b[1] - a[1]);
  let farthest = -1;
  let retained = 0;
  for (const [start, end] of ordered) {
    if (end > farthest) {
      farthest = end;
      retained += 1;
    }
  }
  return retained;
}

const removeCoveredIntervals = solve;
class Solution {
  removeCoveredIntervals(intervals) { return solve(intervals); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeCoveredIntervals };
