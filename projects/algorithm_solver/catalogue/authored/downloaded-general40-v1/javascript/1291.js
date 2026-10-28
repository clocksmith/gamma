'use strict';

// 1291. Sequential Digits (Medium).
// Specification: https://leetcode.com/problems/sequential-digits/description/
function solve(low, high) {
  const result = [];
  for (let length = 2; length <= 9; length++) {
    for (let start = 1; start <= 10 - length; start++) {
      let value = 0;
      for (let digit = 0; digit < length; digit++) value = value * 10 + start + digit;
      if (value >= low && value <= high) result.push(value);
    }
  }
  result.sort((a, b) => a - b);
  return result;
}
const sequentialDigits = solve;
class Solution { sequentialDigits(low, high) { return solve(low, high); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, sequentialDigits };
