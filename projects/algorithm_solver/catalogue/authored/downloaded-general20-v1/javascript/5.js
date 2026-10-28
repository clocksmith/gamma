'use strict';

// 5. Longest Palindromic Substring (Medium).
// Specification: https://leetcode.com/problems/longest-palindromic-substring/description/
function expand(s, left, right) {
  while (left >= 0 && right < s.length && s[left] === s[right]) { left--; right++; }
  return [left + 1, right - left - 1];
}

function solve(s) {
  let start = 0;
  let length = 0;
  for (let center = 0; center < s.length; center++) {
    for (const [candidateStart, candidateLength] of [expand(s, center, center), expand(s, center, center + 1)]) {
      if (candidateLength > length) { start = candidateStart; length = candidateLength; }
    }
  }
  return s.slice(start, start + length);
}

const longestPalindrome = solve;
class Solution {
  longestPalindrome(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestPalindrome };
