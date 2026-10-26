'use strict';

// 1935. Maximum Number of Words You Can Type (Easy).
// Specification: https://leetcode.com/problems/maximum-number-of-words-you-can-type/description/
// O(text length + brokenLetters length) time, O(1) alphabet space; do not allocate word substrings.
function solve(text, brokenLetters) {
  const broken = new Set(brokenLetters);
  let result = 0;
  let blocked = false;
  for (let index = 0; index <= text.length; index++) {
    if (index === text.length || text[index] === ' ') {
      if (!blocked) result++;
      blocked = false;
    } else if (broken.has(text[index])) {
      blocked = true;
    }
  }
  return result;
}

const canBeTypedWords = solve;
class Solution {
  canBeTypedWords(text, brokenLetters) { return solve(text, brokenLetters); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canBeTypedWords };
