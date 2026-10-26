'use strict';

// 2954. Count the Number of Infection Sequences: interleave healthy gaps and count internal infection directions.
// O(n + log MOD) time and O(1) auxiliary space. Inputs are preserved.
function modPow(base, exponent, modulus) {
  let result = 1n;
  while (exponent > 0n) {
    if (exponent & 1n) result = result * base % modulus;
    base = base * base % modulus;
    exponent >>= 1n;
  }
  return result;
}

function solve(n, sick) {
  const modulus = 1000000007n;
  const healthy = n - sick.length;
  let numerator = 1n;
  for (let value = 2; value <= healthy; value += 1) {
    numerator = numerator * BigInt(value) % modulus;
  }
  let denominator = 1n;
  let exponent = 0;
  let previous = -1;
  for (let index = 0; index <= sick.length; index += 1) {
    const position = index < sick.length ? sick[index] : n;
    const gap = position - previous - 1;
    for (let value = 2; value <= gap; value += 1) {
      denominator = denominator * BigInt(value) % modulus;
    }
    if (index > 0 && index < sick.length && gap > 0) exponent += gap - 1;
    previous = position;
  }
  return Number(numerator * modPow(denominator, modulus - 2n, modulus) % modulus
    * modPow(2n, BigInt(exponent), modulus) % modulus);
}

const numberOfSequence = solve;
class Solution {
  numberOfSequence(n, sick) { return solve(n, sick); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfSequence };
