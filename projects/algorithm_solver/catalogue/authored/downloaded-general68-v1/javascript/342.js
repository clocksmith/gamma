'use strict';

// 342. Power of Four (Easy).
// Specification: https://leetcode.com/problems/power-of-four/description/
function solve(n) {
  return n > 0 && (n & (n - 1)) === 0 && (n - 1) % 3 === 0;
}
const isPowerOfFour = solve;
class Solution { isPowerOfFour(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isPowerOfFour };
