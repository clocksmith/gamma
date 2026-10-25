'use strict';

// 2000. Reverse Prefix of Word (Easy).
// Specification: https://leetcode.com/problems/reverse-prefix-of-word/description/
// O(n) time and space. The declared string domain is lowercase ASCII.
function solve(word, ch) {
  const end = word.indexOf(ch);
  if (end === -1) return word;
  return word.slice(0, end + 1).split('').reverse().join('') + word.slice(end + 1);
}

const reversePrefix = solve;
class Solution {
  reversePrefix(word, ch) { return solve(word, ch); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reversePrefix };
