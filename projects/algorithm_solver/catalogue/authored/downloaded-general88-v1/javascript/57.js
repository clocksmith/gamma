'use strict';

// 57. Insert Interval (Medium).
// Specification: https://leetcode.com/problems/insert-interval/description/
function solve(intervals, newInterval) {
  const result = [];
  let inserted = newInterval.slice();
  let used = false;
  for (const interval of intervals) {
    if (interval[1] < inserted[0]) result.push(interval.slice());
    else if (interval[0] > inserted[1]) { if (!used) { result.push(inserted); used = true; } result.push(interval.slice()); }
    else { inserted = [Math.min(inserted[0], interval[0]), Math.max(inserted[1], interval[1])]; }
  }
  if (!used) result.push(inserted);
  return result;
}
const insert = solve;
class Solution { insert(intervals, newInterval) { return solve(intervals, newInterval); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, insert };
