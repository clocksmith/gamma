'use strict';

// 453. Minimum Moves to Equal Array Elements (Medium).
// Specification: https://leetcode.com/problems/minimum-moves-to-equal-array-elements/description/
function solve(nums) {
  const minimum = Math.min(...nums);
  return nums.reduce((sum, value) => sum + (value - minimum), 0);
}
const minMoves = solve;
class Solution { minMoves(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMoves };
