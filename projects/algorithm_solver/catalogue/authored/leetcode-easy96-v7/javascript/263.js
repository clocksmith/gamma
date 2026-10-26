'use strict';

// 263. Ugly Number (Easy).
// Specification: https://leetcode.com/problems/ugly-number/description/
// O(log n) time, O(1) space; remove only factors 2, 3, and 5.
function solve(n) {
  if (n <= 0) return false;
  let value = n;
  for (const factor of [2, 3, 5]) {
    while (value % factor === 0) value /= factor;
  }
  return value === 1;
}

const isUgly = solve;
class Solution {
  isUgly(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isUgly };
