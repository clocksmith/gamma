'use strict';
// 372. Super Pow.
const MODULUS = 1337;
function power(base, exponent) {
  let result = 1; base %= MODULUS;
  while (exponent) { if (exponent & 1) result = result * base % MODULUS; base = base * base % MODULUS; exponent >>= 1; }
  return result;
}
function solve(a, b) {
  let result = 1;
  for (const digit of b) result = power(result, 10) * power(a, digit) % MODULUS;
  return result;
}
const superPow = solve;
class Solution { superPow(a, b) { return solve(a, b); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, superPow };
