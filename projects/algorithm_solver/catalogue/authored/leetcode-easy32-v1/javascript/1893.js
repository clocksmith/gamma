'use strict';

// 1893. Check if All the Integers in a Range Are Covered (Easy).
// Specification: https://leetcode.com/problems/check-if-all-the-integers-in-a-range-are-covered/description/
// O(n + W) time, O(W) space; W = right - left + 1. Preserve intervals.
function solve(ranges, left, right) {
  const width = right - left + 1;
  const changes = new Array(width + 1).fill(0);
  for (const [start, end] of ranges) {
    const first = Math.max(left, start);
    const last = Math.min(right, end);
    if (first <= last) {
      changes[first - left]++;
      changes[last - left + 1]--;
    }
  }
  let coverage = 0;
  for (let offset = 0; offset < width; offset++) {
    coverage += changes[offset];
    if (coverage === 0) return false;
  }
  return true;
}

const isCovered = solve;
class Solution {
  isCovered(ranges, left, right) { return solve(ranges, left, right); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isCovered };
