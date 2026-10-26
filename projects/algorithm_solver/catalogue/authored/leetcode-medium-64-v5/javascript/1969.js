'use strict';

// 1969. Minimum Non-Zero Product of the Array Elements: keep the all-ones maximum and pair the other values into one and maximum-minus-one.
// O(p) modular multiplications and O(p) bits of auxiliary storage; inputs are read-only.
function solve(p) {
  const modulus = 1000000007n;
  const bits = BigInt(p);
  const maximum = (1n << bits) - 1n;
  let exponent = (1n << (bits - 1n)) - 1n;
  let base = (maximum - 1n) % modulus;
  let power = 1n;
  while (exponent > 0n) {
    if (exponent % 2n === 1n) power = power * base % modulus;
    base = base * base % modulus;
    exponent /= 2n;
  }
  return Number((maximum % modulus) * power % modulus);
}

const minNonZeroProduct = solve;
class Solution {
  minNonZeroProduct(p) { return solve(p); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minNonZeroProduct };
