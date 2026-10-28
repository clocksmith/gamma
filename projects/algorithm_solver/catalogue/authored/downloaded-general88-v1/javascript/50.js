'use strict';

// 50. Pow(x, n) (Medium).
// Specification: https://leetcode.com/problems/powx-n/description/
function solve(x, n) {
  if (n < 0) return 1 / solve(x, -n);
  let result = 1; let base = x; let exponent = n;
  while (exponent > 0) { if (exponent % 2 === 1) result *= base; base *= base; exponent = Math.floor(exponent / 2); }
  return result;
}
const myPow = solve;
class Solution { myPow(x, n) { return solve(x, n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, myPow };
