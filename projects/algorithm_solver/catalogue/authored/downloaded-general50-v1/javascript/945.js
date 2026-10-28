'use strict';

// 945. Minimum Increment to Make Array Unique (Medium).
// Specification: https://leetcode.com/problems/minimum-increment-to-make-array-unique/description/
function solve(nums) {
  const sorted = nums.slice().sort((a, b) => a - b);
  let moves = 0;
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i] <= sorted[i - 1]) { moves += sorted[i - 1] + 1 - sorted[i]; sorted[i] = sorted[i - 1] + 1; }
  }
  return moves;
}
const minIncrementForUnique = solve;
class Solution { minIncrementForUnique(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minIncrementForUnique };
