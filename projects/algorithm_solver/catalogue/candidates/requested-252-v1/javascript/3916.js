'use strict';

// 3916. Number of ZigZag Arrays III.
// Specification: https://leetcode.com/problems/number-of-zigzag-arrays-iii/description/
// O(n^3+log MOD) time and O(n) space; exact modular interpolation, n <= 200. Inputs are preserved.
function solve(n, l, r) {
  const modulus = 1000000007;
  const choices = r - l + 1;
  const samples = new Array(n + 1).fill(0);
  // Strict order-preserving maps of the alternating path form a degree-n
  // order polynomial in the number of available values.
  for (let size = 1; size <= n; size++) {
    let counts = new Array(size).fill(1);
    for (let length = 2; length <= n; length++) {
      const next = new Array(size).fill(0);
      let running = 0;
      if (length % 2 === 0) {
        for (let value = 0; value < size; value++) {
          next[value] = running;
          running = (running + counts[value]) % modulus;
        }
      } else {
        for (let value = size - 1; value >= 0; value--) {
          next[value] = running;
          running = (running + counts[value]) % modulus;
        }
      }
      counts = next;
    }
    let total = 0;
    for (const count of counts) total = (total + count) % modulus;
    samples[size] = 2 * total % modulus;
  }
  if (choices <= n) return samples[choices];
  const mod = 1000000007n;
  function power(base, exponent) {
    let answer = 1n;
    while (exponent > 0n) {
      if ((exponent & 1n) !== 0n) answer = answer * base % mod;
      base = base * base % mod;
      exponent >>= 1n;
    }
    return answer;
  }
  const factorial = new Array(n + 1).fill(1n);
  for (let index = 1; index <= n; index++) factorial[index] = factorial[index - 1] * BigInt(index) % mod;
  const inverse = new Array(n + 1).fill(1n);
  inverse[n] = power(factorial[n], mod - 2n);
  for (let index = n; index > 0; index--) inverse[index - 1] = inverse[index] * BigInt(index) % mod;
  const prefix = new Array(n + 2).fill(1n);
  const suffix = new Array(n + 2).fill(1n);
  const x = BigInt(choices);
  for (let index = 0; index <= n; index++) prefix[index + 1] = prefix[index] * (x - BigInt(index)) % mod;
  for (let index = n; index >= 0; index--) suffix[index] = suffix[index + 1] * (x - BigInt(index)) % mod;
  let answer = 0n;
  for (let index = 0; index <= n; index++) {
    let term = BigInt(samples[index]) * prefix[index] % mod * suffix[index + 1] % mod;
    term = term * inverse[index] % mod * inverse[n - index] % mod;
    answer = (answer + ((n - index) % 2 ? -term : term) + mod) % mod;
  }
  return Number(answer);
}

if (typeof module !== 'undefined') module.exports = { solve };
