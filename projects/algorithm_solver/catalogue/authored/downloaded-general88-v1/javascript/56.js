'use strict';

// 56. Merge Intervals (Medium).
// Specification: https://leetcode.com/problems/merge-intervals/description/
function solve(intervals) {
  const sorted = intervals.slice().sort((a, b) => a[0] - b[0]);
  const result = [];
  for (const interval of sorted) {
    if (result.length === 0 || interval[0] > result[result.length - 1][1]) result.push(interval.slice());
    else result[result.length - 1][1] = Math.max(result[result.length - 1][1], interval[1]);
  }
  return result;
}
const merge = solve;
class Solution { merge(intervals) { return solve(intervals); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, merge };
