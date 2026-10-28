'use strict';

// 462. Minimum Moves to Equal Array Elements II (Medium).
// Specification: https://leetcode.com/problems/minimum-moves-to-equal-array-elements-ii/description/
function solve(nums) {
  const sorted = nums.slice().sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)];
  return sorted.reduce((sum, value) => sum + Math.abs(value - median), 0);
}
const minMoves2 = solve;
class Solution { minMoves2(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMoves2 };
