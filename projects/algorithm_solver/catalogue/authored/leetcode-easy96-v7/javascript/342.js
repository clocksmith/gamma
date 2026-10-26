'use strict';

// 342. Power of Four (Easy).
// Specification: https://leetcode.com/problems/power-of-four/description/
// O(log n) time, O(1) space; repeatedly divide by four without floating logarithms.
function solve(n) {
  if (n <= 0) return false;
  let value = n;
  while (value % 4 === 0) value /= 4;
  return value === 1;
}

const isPowerOfFour = solve;
class Solution {
  isPowerOfFour(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isPowerOfFour };
