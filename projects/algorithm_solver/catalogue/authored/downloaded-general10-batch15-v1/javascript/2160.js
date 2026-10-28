'use strict';

// 2160. Minimum Sum of Four Digit Number After Splitting Digits (Easy).
// Specification: https://leetcode.com/problems/minimum-sum-of-four-digit-number-after-splitting-digits/description/
function solve(num) {
  const digits = String(num).split('').map(Number).sort((a, b) => a - b);
  return (digits[0] * 10 + digits[2]) + (digits[1] * 10 + digits[3]);
}
const minimumSum = solve;
class Solution { minimumSum(num) { return solve(num); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumSum };
