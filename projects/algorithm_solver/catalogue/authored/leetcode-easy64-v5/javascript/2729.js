'use strict';

// 2729. Check if The Number is Fascinating (Easy).
// Specification: https://leetcode.com/problems/check-if-the-number-is-fascinating/description/
// O(1) time and space for the three-digit input domain.
function solve(n) {
  const digits = String(n) + String(2 * n) + String(3 * n);
  if (digits.length !== 9) return false;
  const seen = new Set();
  for (const digit of digits) {
    if (digit === '0' || seen.has(digit)) return false;
    seen.add(digit);
  }
  return true;
}

const isFascinating = solve;
class Solution {
  isFascinating(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isFascinating };
