'use strict';

// 436. Find Right Interval (Medium).
// Specification: https://leetcode.com/problems/find-right-interval/description/
function solve(intervals) {
  const starts = intervals.map((interval, index) => [interval[0], index]).sort((a, b) => a[0] - b[0]);
  const result = [];
  for (const interval of intervals) {
    let left = 0; let right = starts.length - 1; let answer = -1;
    while (left <= right) {
      const mid = Math.floor((left + right) / 2);
      if (starts[mid][0] >= interval[1]) { answer = starts[mid][1]; right = mid - 1; } else left = mid + 1;
    }
    result.push(answer);
  }
  return result;
}
const findRightInterval = solve;
class Solution { findRightInterval(intervals) { return solve(intervals); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findRightInterval };
