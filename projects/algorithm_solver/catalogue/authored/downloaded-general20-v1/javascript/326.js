'use strict';

// 326. Power of Three (Easy).
// Specification: https://leetcode.com/problems/power-of-three/description/
function solve(n) {
  return n > 0 && 1162261467 % n === 0;
}

const isPowerOfThree = solve;
class Solution {
  isPowerOfThree(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isPowerOfThree };
