'use strict';

// 659. Split Array into Consecutive Subsequences (Medium).
// Specification: https://leetcode.com/problems/split-array-into-consecutive-subsequences/description/
function solve(nums) {
  const counts = new Map();
  for (const value of nums) counts.set(value, (counts.get(value) || 0) + 1);
  const tails = new Map();
  for (const value of nums) {
    if ((counts.get(value) || 0) === 0) continue;
    counts.set(value, counts.get(value) - 1);
    if ((tails.get(value - 1) || 0) > 0) {
      tails.set(value - 1, tails.get(value - 1) - 1);
      tails.set(value, (tails.get(value) || 0) + 1);
    } else if ((counts.get(value + 1) || 0) > 0 && (counts.get(value + 2) || 0) > 0) {
      counts.set(value + 1, counts.get(value + 1) - 1);
      counts.set(value + 2, counts.get(value + 2) - 1);
      tails.set(value + 2, (tails.get(value + 2) || 0) + 1);
    } else return false;
  }
  return true;
}
const isPossible = solve;
class Solution { isPossible(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isPossible };
