'use strict';

// 1830. Minimum Number of Operations to Make String Sorted: multiset lexicographic rank modulo a prime.
// O(26*n + log MOD) time and O(n) auxiliary space. Inputs are preserved.
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
  const length = s.length;
  const factorial = Array(length + 1).fill(1n);
  for (let index = 1; index <= length; index += 1) factorial[index] = factorial[index - 1] * BigInt(index) % modulus;
  const inverse = Array(length + 1).fill(1n);
  inverse[length] = modPow(factorial[length], modulus - 2n, modulus);
  for (let index = length; index > 0; index -= 1) inverse[index - 1] = inverse[index] * BigInt(index) % modulus;
  const counts = new Int32Array(26);
  for (const character of s) counts[character.charCodeAt(0) - 97] += 1;
  let denominatorInverse = 1n;
  for (const count of counts) denominatorInverse = denominatorInverse * inverse[count] % modulus;
  let answer = 0n;
  for (let position = 0; position < length; position += 1) {
    const index = s.charCodeAt(position) - 97;
    let smaller = 0;
    for (let letter = 0; letter < index; letter += 1) smaller += counts[letter];
    answer = (answer + BigInt(smaller) * factorial[length - position - 1] * denominatorInverse) % modulus;
    denominatorInverse = denominatorInverse * BigInt(counts[index]) % modulus;
    counts[index] -= 1;
  }
  return Number(answer);
}

const makeStringSorted = solve;
class Solution {
  makeStringSorted(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, makeStringSorted };
