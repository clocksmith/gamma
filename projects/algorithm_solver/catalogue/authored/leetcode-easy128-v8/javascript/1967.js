'use strict';

// 1967. Number of Strings That Appear as Substrings in Word (Easy).
// Specification: https://leetcode.com/problems/number-of-strings-that-appear-as-substrings-in-word/description/
// O(word length * total pattern length) worst-case time, O(1) auxiliary space; count repeated pattern entries separately.
function solve(patterns, word) {
  let count = 0;
  for (const pattern of patterns) {
    if (word.includes(pattern)) count++;
  }
  return count;
}

const numOfStrings = solve;
class Solution {
  numOfStrings(patterns, word) { return solve(patterns, word); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numOfStrings };
