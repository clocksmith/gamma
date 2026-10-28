'use strict';

// 680. Valid Palindrome II (Easy).
// Specification: https://leetcode.com/problems/valid-palindrome-ii/description/
function isPalindromeRange(s, left, right) {
  while (left < right) { if (s[left] !== s[right]) return false; left++; right--; }
  return true;
}
function solve(s) {
  let left = 0; let right = s.length - 1;
  while (left < right) {
    if (s[left] !== s[right]) return isPalindromeRange(s, left + 1, right) || isPalindromeRange(s, left, right - 1);
    left++; right--;
  }
  return true;
}
const validPalindrome = solve;
class Solution { validPalindrome(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, validPalindrome };
