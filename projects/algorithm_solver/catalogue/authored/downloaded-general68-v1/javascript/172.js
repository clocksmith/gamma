'use strict';

// 172. Factorial Trailing Zeroes (Medium).
// Specification: https://leetcode.com/problems/factorial-trailing-zeroes/description/
function solve(n) {
  let count = 0;
  while (n > 0) { n = Math.floor(n / 5); count += n; }
  return count;
}
const trailingZeroes = solve;
class Solution { trailingZeroes(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, trailingZeroes };
