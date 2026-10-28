'use strict';

// 136. Single Number (Easy).
// Specification: https://leetcode.com/problems/single-number/description/
function solve(nums) {
  let result = 0;
  for (const value of nums) result ^= value;
  return result;
}
const singleNumber = solve;
class Solution { singleNumber(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, singleNumber };
