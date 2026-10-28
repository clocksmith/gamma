'use strict';

// 878. Nth Magical Number (Hard).
// Specification: https://leetcode.com/problems/nth-magical-number/description/
function gcd(a, b) { while (b !== 0) { const t = a % b; a = b; b = t; } return a; }
function solve(n, a, b) {
  const MOD = 1000000007;
  const lcm = a * b / gcd(a, b);
  let lo = 1; let hi = n * Math.min(a, b);
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    const count = Math.floor(mid / a) + Math.floor(mid / b) - Math.floor(mid / lcm);
    if (count >= n) hi = mid; else lo = mid + 1;
  }
  return lo % MOD;
}
const nthMagicalNumber = solve;
class Solution { nthMagicalNumber(n, a, b) { return solve(n, a, b); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, nthMagicalNumber };
