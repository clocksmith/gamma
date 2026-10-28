'use strict';

// 1903. Largest Odd Number in String (Easy).
// Specification: https://leetcode.com/problems/largest-odd-number-in-string/description/
function solve(num) {
  for (let i = num.length - 1; i >= 0; i--) {
    if ((num.charCodeAt(i) - 48) % 2 === 1) return num.slice(0, i + 1);
  }
  return '';
}
const largestOddNumber = solve;
class Solution { largestOddNumber(num) { return solve(num); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestOddNumber };
