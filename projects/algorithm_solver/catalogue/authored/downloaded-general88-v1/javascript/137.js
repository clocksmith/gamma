'use strict';

// 137. Single Number II (Medium).
// Specification: https://leetcode.com/problems/single-number-ii/description/
function solve(nums) {
  let ones = 0; let twos = 0;
  for (const value of nums) {
    ones = (ones ^ value) & ~twos;
    twos = (twos ^ value) & ~ones;
  }
  return ones;
}
const singleNumber = solve;
class Solution { singleNumber(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, singleNumber };
