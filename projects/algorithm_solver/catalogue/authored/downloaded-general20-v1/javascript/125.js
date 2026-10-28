'use strict';

// 125. Valid Palindrome (Easy).
// Specification: https://leetcode.com/problems/valid-palindrome/description/
function isAlphanumeric(ch) {
  return (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') || (ch >= '0' && ch <= '9');
}

function solve(s) {
  let left = 0;
  let right = s.length - 1;
  while (left < right) {
    while (left < right && !isAlphanumeric(s[left])) left++;
    while (left < right && !isAlphanumeric(s[right])) right--;
    if (s[left].toLowerCase() !== s[right].toLowerCase()) return false;
    left++; right--;
  }
  return true;
}

const isPalindrome = solve;
class Solution {
  isPalindrome(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isPalindrome };
