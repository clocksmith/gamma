'use strict';

// 479. Largest Palindrome Product. Enumerate even-length palindromes in descending order with exact integer factor checks.

function solve(n) {
  if (n === 1) return 9;
  const upper = 10n ** BigInt(n) - 1n, lower = 10n ** BigInt(n - 1), maximum = upper * upper;
  for (let half = upper; half >= lower; half -= 1n) {
    const text = String(half), palindrome = BigInt(text + text.split('').reverse().join(''));
    if (palindrome > maximum) continue;
    const quotientBound = (palindrome + upper - 1n) / upper;
    const minimumFactor = quotientBound > lower ? quotientBound : lower;
    for (let factor = upper - upper % 11n; factor >= minimumFactor; factor -= 11n) {
      if (palindrome % factor === 0n) {
        const other = palindrome / factor;
        if (other >= lower && other <= upper) return Number(palindrome % 1337n);
      }
    }
  }
  return 0;
}

const largestPalindrome = solve;
class Solution {
  largestPalindrome(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestPalindrome };
