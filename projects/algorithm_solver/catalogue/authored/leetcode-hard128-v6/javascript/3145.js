'use strict';

// 3145. Find Products of Elements of Big Array.
// Binary search complete integer blocks using set-bit counts, then sum their exponents; O(q*log^2 M) time. JavaScript uses BigInt for large index arithmetic.

function solve(queries) {
  function statistics(limit) {
    let count = 0n, exponent = 0n, power = 1n, bit = 0n;
    while (power <= limit) {
      const cycle = 2n * power, remainder = (limit + 1n) % cycle;
      const ones = (limit + 1n) / cycle * power + (remainder > power ? remainder - power : 0n);
      count += ones; exponent += bit * ones; power *= 2n; bit += 1n;
    }
    return [count, exponent];
  }
  function prefix(length) {
    let low = 0n, high = length;
    while (low < high) {
      const middle = (low + high + 1n) / 2n;
      if (statistics(middle)[0] <= length) low = middle; else high = middle - 1n;
    }
    let [complete, exponent] = statistics(low), remaining = length - complete, bit = 0n;
    const value = low + 1n;
    while (remaining > 0n) {
      if (((value >> bit) & 1n) !== 0n) { exponent += bit; remaining -= 1n; }
      bit += 1n;
    }
    return exponent;
  }
  return queries.map(([left, right, modulus]) => {
    const mod = BigInt(modulus);
    let exponent = prefix(BigInt(right) + 1n) - prefix(BigInt(left)), base = 2n % mod, result = 1n % mod;
    while (exponent > 0n) {
      if ((exponent & 1n) !== 0n) result = result * base % mod;
      base = base * base % mod; exponent >>= 1n;
    }
    return Number(result);
  });
}

const findProductsOfElements = solve;
class Solution {
  findProductsOfElements(queries) { return solve(queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findProductsOfElements };
