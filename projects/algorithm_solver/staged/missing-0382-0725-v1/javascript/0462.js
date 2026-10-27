'use strict';

// 462. Minimum Moves to Equal Array Elements II.

function solve(nums) {
  const ordered = nums.slice().sort((a, b) => a - b), median = ordered[Math.floor(ordered.length / 2)];
  return ordered.reduce((sum, value) => sum + Math.abs(value - median), 0);
}

const minMoves2 = solve;
class Solution {
  minMoves2(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMoves2 };
