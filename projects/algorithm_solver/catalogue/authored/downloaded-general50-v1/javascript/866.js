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
function isPalindrome(x) { const s = String(x); return s === [...s].reverse().join(''); }
function solve(n) {
  let x = n;
  while (true) {
    if (isPalindrome(x) && isPrime(x)) return x;
    x++;
    if (x > 11 && x < 100 && x % 2 === 0) continue;
  }
}
const primePalindrome = solve;
class Solution { primePalindrome(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, primePalindrome };
