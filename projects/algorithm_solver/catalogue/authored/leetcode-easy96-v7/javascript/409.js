'use strict';

// 409. Longest Palindrome (Easy).
// Specification: https://leetcode.com/problems/longest-palindrome/description/
// O(n) expected time, O(a) space; pair equal case-sensitive letters and allow one center.
function solve(s) {
  const counts = new Map();
  for (const character of s) counts.set(character, (counts.get(character) || 0) + 1);
  let length = 0;
  let hasOdd = false;
  for (const count of counts.values()) {
    length += count - count % 2;
    if (count % 2 !== 0) hasOdd = true;
  }
  return length + (hasOdd ? 1 : 0);
}

const longestPalindrome = solve;
class Solution {
  longestPalindrome(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestPalindrome };
