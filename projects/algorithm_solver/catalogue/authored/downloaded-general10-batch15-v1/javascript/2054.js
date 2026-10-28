'use strict';

// 2054. Two Best Non-Overlapping Events (Medium).
// Specification: https://leetcode.com/problems/two-best-non-overlapping-events/description/
function solve(events) {
  const sorted = events.map((e) => e.slice()).sort((a, b) => a[0] - b[0]);
  const n = sorted.length;
  const suffix = new Array(n + 1).fill(0);
  for (let i = n - 1; i >= 0; i--) suffix[i] = Math.max(suffix[i + 1], sorted[i][2]);
  let best = 0;
  for (const event of sorted) {
    let left = 0; let right = n;
    while (left < right) {
      const mid = (left + right) >> 1;
      if (sorted[mid][0] > event[1]) right = mid; else left = mid + 1;
    }
    const value = event[2] + (left < n ? suffix[left] : 0);
    best = Math.max(best, value);
  }
  return best;
}
const maxTwoEvents = solve;
class Solution { maxTwoEvents(events) { return solve(events); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxTwoEvents };
