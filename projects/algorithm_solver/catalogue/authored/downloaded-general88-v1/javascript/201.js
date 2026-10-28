'use strict';

// 201. Bitwise AND of Numbers Range (Medium).
// Specification: https://leetcode.com/problems/bitwise-and-of-numbers-range/description/
function solve(left, right) {
  let shift = 0;
  while (left < right) { left = Math.floor(left / 2); right = Math.floor(right / 2); shift++; }
  return left * (2 ** shift);
}
const rangeBitwiseAnd = solve;
class Solution { rangeBitwiseAnd(left, right) { return solve(left, right); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, rangeBitwiseAnd };
