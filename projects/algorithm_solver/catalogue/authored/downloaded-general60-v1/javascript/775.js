'use strict';

// 775. Global and Local Inversions (Medium).
// Specification: https://leetcode.com/problems/global-and-local-inversions/description/
function solve(nums) {
  for (let i = 0; i < nums.length; i++) { if (Math.abs(nums[i] - i) > 1) return false; }
  return true;
}
const isIdealPermutation = solve;
class Solution { isIdealPermutation(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isIdealPermutation };
