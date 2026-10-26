'use strict';

// 231. Power of Two (Easy).
// Specification: https://leetcode.com/problems/power-of-two/description/
// O(log n) time, O(1) space; use exact integer division on the signed 32-bit domain.
function solve(n) {
  if (n <= 0) return false;
  let value = n;
  while (value % 2 === 0) value /= 2;
  return value === 1;
}

const isPowerOfTwo = solve;
class Solution {
  isPowerOfTwo(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isPowerOfTwo };
