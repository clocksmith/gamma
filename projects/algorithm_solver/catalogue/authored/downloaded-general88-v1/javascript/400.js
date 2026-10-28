'use strict';

// 400. Nth Digit (Medium).
// Specification: https://leetcode.com/problems/nth-digit/description/
function solve(n) {
  let digits = 1; let count = 9; let start = 1;
  while (n > digits * count) { n -= digits * count; digits++; count *= 10; start *= 10; }
  const number = start + Math.floor((n - 1) / digits);
  const index = (n - 1) % digits;
  return Number(String(number)[index]);
}
const findNthDigit = solve;
class Solution { findNthDigit(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findNthDigit };
