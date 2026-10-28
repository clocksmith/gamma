'use strict';

// 9. Palindrome Number (Easy).
// Specification: https://leetcode.com/problems/palindrome-number/description/
function solve(x) {
  if (x < 0) return false;
  let reversed = 0;
  let value = x;
  while (value !== 0) { reversed = reversed * 10 + (value % 10); value = Math.trunc(value / 10); }
  return reversed === x;
}
const isPalindrome = solve;
class Solution { isPalindrome(x) { return solve(x); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isPalindrome };
