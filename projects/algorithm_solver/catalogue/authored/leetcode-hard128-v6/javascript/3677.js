'use strict';

// 3677. Count Binary Palindromic Numbers.
// Count shorter palindrome lengths and unrank the leading half at the bound length, including zero; O(log n) arithmetic operations and space. Inputs are preserved.

function solve(n) {
  const bound = BigInt(n);
  if (bound === 0n) return 1;
  const bits = bound.toString(2), length = bits.length;
  let answer = 1n;
  for (let size = 1; size < length; size += 1) answer += 1n << BigInt(Math.ceil(size / 2) - 1);
  const half = Math.ceil(length / 2), prefix = bits.slice(0, half);
  answer += BigInt('0b' + prefix) - (1n << BigInt(half - 1));
  const reflected = length % 2 ? prefix.slice(0, -1) : prefix;
  const palindrome = BigInt('0b' + prefix + reflected.split('').reverse().join(''));
  if (palindrome <= bound) answer += 1n;
  return Number(answer);
}

const countBinaryPalindromes = solve;
class Solution {
  countBinaryPalindromes(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countBinaryPalindromes };
