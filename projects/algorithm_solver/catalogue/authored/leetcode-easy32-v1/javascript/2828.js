'use strict';

// 2828. Check if a String Is an Acronym of Words (Easy).
// Specification: https://leetcode.com/problems/check-if-a-string-is-an-acronym-of-words/description/
// O(words.length) time, O(1) space. Words are nonempty lowercase ASCII strings.
function solve(words, s) {
  if (words.length !== s.length) return false;
  for (let index = 0; index < words.length; index++) {
    if (words[index][0] !== s[index]) return false;
  }
  return true;
}

const isAcronym = solve;
class Solution {
  isAcronym(words, s) { return solve(words, s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isAcronym };
