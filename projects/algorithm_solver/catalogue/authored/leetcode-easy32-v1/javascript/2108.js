'use strict';

// 2108. Find First Palindromic String in the Array (Easy).
// Specification: https://leetcode.com/problems/find-first-palindromic-string-in-the-array/description/
// O(total characters) time, O(1) space. Preserve the input word order.
function solve(words) {
  for (const word of words) {
    let left = 0;
    let right = word.length - 1;
    while (left < right && word[left] === word[right]) {
      left++;
      right--;
    }
    if (left >= right) return word;
  }
  return '';
}

const firstPalindrome = solve;
class Solution {
  firstPalindrome(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, firstPalindrome };
