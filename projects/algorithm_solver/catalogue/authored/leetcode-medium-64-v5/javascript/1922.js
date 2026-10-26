'use strict';

// 1922. Count Good Numbers: multiply independent even-position and odd-position choices with modular exponentiation.
// O(log(n + 1)) modular multiplications and O(1) bounded auxiliary storage; inputs are read-only.
function solve(n) {
  const modulus = 1000000007n;
  const length = BigInt(n);
  function power(base, exponent) {
    let result = 1n;
    while (exponent > 0n) {
      if (exponent % 2n === 1n) result = result * base % modulus;
      base = base * base % modulus;
      exponent /= 2n;
    }
    return result;
  }
  return Number(power(5n, (length + 1n) / 2n) * power(4n, length / 2n) % modulus);
}

const countGoodNumbers = solve;
class Solution {
  countGoodNumbers(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countGoodNumbers };
