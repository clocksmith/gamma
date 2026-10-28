'use strict';

// 1272. Remove Interval (Medium).
// Specification: https://leetcode.com/problems/remove-interval/description/
function solve(intervals, toBeRemoved) {
  const [removeStart, removeEnd] = toBeRemoved;
  const result = [];
  for (const [start, end] of intervals) {
    if (end <= removeStart || start >= removeEnd) result.push([start, end]);
    else {
      if (start < removeStart) result.push([start, removeStart]);
      if (end > removeEnd) result.push([removeEnd, end]);
    }
  }
  return result;
}
const removeInterval = solve;
class Solution { removeInterval(intervals, toBeRemoved) { return solve(intervals, toBeRemoved); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeInterval };
