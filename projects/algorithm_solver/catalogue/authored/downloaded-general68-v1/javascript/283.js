'use strict';

// 283. Move Zeroes (Easy).
// Specification: https://leetcode.com/problems/move-zeroes/description/
function solve(nums) {
  const result = nums.filter((value) => value !== 0);
  while (result.length < nums.length) result.push(0);
  return result;
}
const moveZeroes = solve;
class Solution { moveZeroes(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, moveZeroes };
