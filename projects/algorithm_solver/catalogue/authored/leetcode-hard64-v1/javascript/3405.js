'use strict';

// 3405. Count the Number of Arrays with K Matching Adjacent Elements: choose equal boundaries and color the remaining runs.
// O(min(k,n-1-k) + log MOD + log n) time and O(1) auxiliary space. Inputs are preserved.
function modPow(base, exponent, modulus) {
  let result = 1n;
  while (exponent > 0n) {
    if (exponent & 1n) result = result * base % modulus;
    base = base * base % modulus;
    exponent >>= 1n;
  }
  return result;
}

function solve(n, m, k) {
  const modulus = 1000000007n;
  const chosen = Math.min(k, n - 1 - k);
  let numerator = 1n;
  let denominator = 1n;
  for (let index = 0; index < chosen; index += 1) {
    numerator = numerator * BigInt(n - 1 - index) % modulus;
    denominator = denominator * BigInt(index + 1) % modulus;
  }
  const combinations = numerator * modPow(denominator, modulus - 2n, modulus) % modulus;
  return Number(BigInt(m) * modPow(BigInt(m - 1), BigInt(n - 1 - k), modulus) % modulus
    * combinations % modulus);
}

const countGoodArrays = solve;
class Solution {
  countGoodArrays(n, m, k) { return solve(n, m, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countGoodArrays };
