'use strict';

// 2514. Count Anagrams: per-word multinomials with one modular inverse.
// O(n + log MOD) time and O(n) auxiliary space for split words. Inputs are preserved.
function modPow(base, exponent, modulus) {
  let result = 1n;
  while (exponent > 0n) {
    if (exponent & 1n) result = result * base % modulus;
    base = base * base % modulus;
    exponent >>= 1n;
  }
  return result;
}

function solve(s) {
  const modulus = 1000000007n;
  let numerator = 1n;
  let denominator = 1n;
  for (const word of s.split(' ')) {
    for (let factor = 2; factor <= word.length; factor += 1) numerator = numerator * BigInt(factor) % modulus;
    const counts = new Int32Array(26);
    for (const character of word) counts[character.charCodeAt(0) - 97] += 1;
    for (const count of counts) {
      for (let factor = 2; factor <= count; factor += 1) denominator = denominator * BigInt(factor) % modulus;
    }
  }
  return Number(numerator * modPow(denominator, modulus - 2n, modulus) % modulus);
}

const countAnagrams = solve;
class Solution {
  countAnagrams(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countAnagrams };
