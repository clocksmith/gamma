'use strict';

// 3908. Valid Digit Number (Easy).
// Specification: https://leetcode.com/problems/valid-digit-number/description/
// O(d) time and space; use the ordinary decimal representation, including zero.
function solve(n, x) {
  const digits = String(n);
  const target = String(x);
  return digits[0] !== target && digits.includes(target);
}

const validDigit = solve;
class Solution {
  validDigit(n, x) { return solve(n, x); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, validDigit };
