'use strict';

// 151. Reverse Words in a String (Medium).
// Specification: https://leetcode.com/problems/reverse-words-in-a-string/description/
function solve(s) {
  return s.trim().split(/\s+/).reverse().join(' ');
}
const reverseWords = solve;
class Solution { reverseWords(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseWords };
