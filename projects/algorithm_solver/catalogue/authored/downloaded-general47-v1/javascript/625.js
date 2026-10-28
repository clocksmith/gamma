'use strict';

// 625. Minimum Factorization (Medium).
// Specification: https://leetcode.com/problems/minimum-factorization/description/
function solve(a) {
  if (a < 10) return a;
  const digits = [];
  let value = a;
  for (let divisor = 9; divisor >= 2; divisor--) {
    while (value % divisor === 0) { digits.push(divisor); value = Math.floor(value / divisor); }
  }
  if (value !== 1) return 0;
  digits.sort((x, y) => x - y);
  const result = Number(digits.join(''));
  return result > 2147483647 ? 0 : result;
}
const smallestFactorization = solve;
class Solution { smallestFactorization(a) { return solve(a); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestFactorization };
