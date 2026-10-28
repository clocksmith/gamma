'use strict';

// 128. Longest Consecutive Sequence (Medium).
// Specification: https://leetcode.com/problems/longest-consecutive-sequence/description/
function solve(nums) {
  const seen = new Set(nums);
  let best = 0;
  for (const value of seen) {
    if (!seen.has(value - 1)) {
      let length = 1; let current = value;
      while (seen.has(current + 1)) { current++; length++; }
      best = Math.max(best, length);
    }
  }
  return best;
}
const longestConsecutive = solve;
class Solution { longestConsecutive(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestConsecutive };
