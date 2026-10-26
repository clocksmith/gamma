'use strict';

// 3856. Trim Trailing Vowels (Easy).
// Specification: https://leetcode.com/problems/trim-trailing-vowels/description/
// O(n) time and output space; remove only the trailing lowercase vowels.
function solve(s) {
  let end = s.length;
  while (end > 0 && 'aeiou'.includes(s[end - 1])) end--;
  return s.slice(0, end);
}

const trimTrailingVowels = solve;
class Solution {
  trimTrailingVowels(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, trimTrailingVowels };
