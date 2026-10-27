'use strict';

// 680. Valid Palindrome II.

function solve(s) {
  function palindrome(left, right) {
    while (left < right) { if (s[left++] !== s[right--]) return false; }
    return true;
  }
  let left = 0, right = s.length - 1;
  while (left < right) {
    if (s[left] !== s[right]) return palindrome(left + 1, right) || palindrome(left, right - 1);
    left += 1; right -= 1;
  }
  return true;
}

const validPalindrome = solve;
class Solution {
  validPalindrome(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, validPalindrome };
