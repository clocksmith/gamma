'use strict';

// 738. Monotone Increasing Digits (Medium).
// Specification: https://leetcode.com/problems/monotone-increasing-digits/description/
function solve(n) {
  const digits = [...String(n)];
  let marker = digits.length;
  for (let i = digits.length - 1; i > 0; i--) {
    if (digits[i] < digits[i - 1]) { digits[i - 1] = String(Number(digits[i - 1]) - 1); marker = i; }
  }
  for (let i = marker; i < digits.length; i++) digits[i] = '9';
  return Number(digits.join(''));
}
const monotoneIncreasingDigits = solve;
class Solution { monotoneIncreasingDigits(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, monotoneIncreasingDigits };
