'use strict';

// 260. Single Number III (Medium).
// Specification: https://leetcode.com/problems/single-number-iii/description/
function solve(nums) {
  let xor = 0;
  for (const value of nums) xor ^= value;
  const bit = xor & -xor;
  let first = 0; let second = 0;
  for (const value of nums) { if ((value & bit) !== 0) first ^= value; else second ^= value; }
  return [first, second].sort((a, b) => a - b);
}
const singleNumber = solve;
class Solution { singleNumber(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, singleNumber };
