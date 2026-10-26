'use strict';

// 58. Length of Last Word (Easy).
// Specification: https://leetcode.com/problems/length-of-last-word/description/
// O(n) time, O(1) space; skip trailing spaces and scan the final word.
function solve(s) {
  let index = s.length - 1;
  while (index >= 0 && s[index] === ' ') index--;
  const end = index;
  while (index >= 0 && s[index] !== ' ') index--;
  return end - index;
}

const lengthOfLastWord = solve;
class Solution {
  lengthOfLastWord(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, lengthOfLastWord };
