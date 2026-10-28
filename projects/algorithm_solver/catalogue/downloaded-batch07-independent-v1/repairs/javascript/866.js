'use strict';

// 866. Prime Palindrome (Medium).
// Specification: https://leetcode.com/problems/prime-palindrome/description/
function isPrime(x) {
  if (x < 2) return false;
  if (x === 2) return true;
  if (x % 2 === 0) return false;
  for (let d = 3; d * d <= x; d += 2) { if (x % d === 0) return false; }
  return true;
}
function solve(n) {
  // Every even-digit palindrome is divisible by 11; only 11 is prime.
  for (const small of [2, 3, 5, 7, 11]) if (n <= small) return small;
  let digits = String(n).length;
  if (digits % 2 === 0) digits++;
  while (true) {
    const half = (digits + 1) / 2;
    const first = Math.max(10 ** (half - 1),
      String(n).length === digits ? Number(String(n).slice(0, half)) : 0);
    for (let prefix = first; prefix < 10 ** half; prefix++) {
      const text = String(prefix);
      const palindrome = Number(text + text.slice(0, -1).split('').reverse().join(''));
      if (palindrome >= n && isPrime(palindrome)) return palindrome;
    }
    digits += 2;
  }
}
const primePalindrome = solve;
class Solution { primePalindrome(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, primePalindrome };
