'use strict';

// 1201. Ugly Number III (Medium).
// Specification: https://leetcode.com/problems/ugly-number-iii/description/
function gcd(a, b) { while (b !== 0) { const t = a % b; a = b; b = t; } return a; }
function lcm(a, b) { return Math.floor(a / gcd(a, b)) * b; }
function countUgly(n, a, b, c) {
  return Math.floor(n / a) + Math.floor(n / b) + Math.floor(n / c) - Math.floor(n / lcm(a, b)) - Math.floor(n / lcm(b, c)) - Math.floor(n / lcm(a, c)) + Math.floor(n / lcm(a, lcm(b, c)));
}
function solve(n, a, b, c) {
  let left = 1; let right = 2000000000;
  while (left < right) {
    const mid = Math.floor((left + right) / 2);
    if (countUgly(mid, a, b, c) >= n) right = mid; else left = mid + 1;
  }
  return left;
}
const nthUglyNumber = solve;
class Solution { nthUglyNumber(n, a, b, c) { return solve(n, a, b, c); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, nthUglyNumber };
