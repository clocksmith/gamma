'use strict';

// 2851. String Transformation. KMP counts matching rotations and a two-state matrix counts suffix moves; O(n+log k) time and O(n) space. Inputs are preserved.

function solve(s, t, k) {
  const modulus = 1000000007n;
  const size = s.length;
  const prefix = Array(size).fill(0);
  for (let index = 1; index < size; index += 1) {
    let length = prefix[index - 1];
    while (length > 0 && t[index] !== t[length]) length = prefix[length - 1];
    if (t[index] === t[length]) length += 1;
    prefix[index] = length;
  }
  let matches = 0;
  let length = 0;
  for (let index = 0; index < 2 * size - 1; index += 1) {
    const char = s[index % size];
    while (length > 0 && char !== t[length]) length = prefix[length - 1];
    if (char === t[length]) length += 1;
    if (length === size) { matches += 1; length = prefix[length - 1]; }
  }
  if (matches === 0) return 0;
  let exponent = BigInt(k);
  if (matches === size) {
    let base = BigInt(size - 1);
    let answer = 1n;
    while (exponent > 0n) {
      if ((exponent & 1n) !== 0n) answer = answer * base % modulus;
      base = base * base % modulus;
      exponent >>= 1n;
    }
    return Number(answer);
  }
  function multiply(first, second) {
    return [
      (first[0] * second[0] + first[1] * second[2]) % modulus,
      (first[0] * second[1] + first[1] * second[3]) % modulus,
      (first[2] * second[0] + first[3] * second[2]) % modulus,
      (first[2] * second[1] + first[3] * second[3]) % modulus,
    ];
  }
  let result = [1n, 0n, 0n, 1n];
  let transition = [matches - 1, matches, size - matches, size - matches - 1].map(value => BigInt(value));
  while (exponent > 0n) {
    if ((exponent & 1n) !== 0n) result = multiply(result, transition);
    transition = multiply(transition, transition);
    exponent >>= 1n;
  }
  return Number(s === t ? result[0] : result[1]);
}

const numberOfWays = solve;
class Solution {
  numberOfWays(s, t, k) { return solve(s, t, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfWays };
