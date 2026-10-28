'use strict';

// 557. Reverse Words in a String III (Easy).
// Specification: https://leetcode.com/problems/reverse-words-in-a-string-iii/description/
function solve(s) {
  return s.split(' ').map((word) => [...word].reverse().join('')).join(' ');
}

const reverseWords = solve;
class Solution {
  reverseWords(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseWords };
