'use strict';

// 343. Integer Break (Medium).
// Specification: https://leetcode.com/problems/integer-break/description/
function solve(n) {
  if (n <= 3) return n - 1;
  let result = 1;
  while (n > 4) { result *= 3; n -= 3; }
  return result * n;
}
const integerBreak = solve;
class Solution { integerBreak(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, integerBreak };
