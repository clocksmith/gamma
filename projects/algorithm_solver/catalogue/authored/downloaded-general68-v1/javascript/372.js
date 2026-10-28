'use strict';

// 372. Super Pow (Medium).
// Specification: https://leetcode.com/problems/super-pow/description/
function powMod(base, exponent, modulus) {
  let result = 1;
  let value = base % modulus;
  for (let i = 0; i < exponent; i++) result = (result * value) % modulus;
  return result;
}
function solve(a, b) {
  let result = 1;
  for (const digit of b) result = (powMod(result, 10, 1337) * powMod(a, digit, 1337)) % 1337;
  return result;
}
const superPow = solve;
class Solution { superPow(a, b) { return solve(a, b); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, superPow };
