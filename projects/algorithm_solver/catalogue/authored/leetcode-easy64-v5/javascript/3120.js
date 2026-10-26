'use strict';

// 3120. Count the Number of Special Characters I (Easy).
// Specification: https://leetcode.com/problems/count-the-number-of-special-characters-i/description/
// O(n) time, O(1) alphabet space; order of lowercase and uppercase occurrences is irrelevant.
function solve(word) {
  const lower = new Array(26).fill(false);
  const upper = new Array(26).fill(false);
  for (const character of word) {
    const code = character.charCodeAt(0);
    if (code >= 97) lower[code - 97] = true;
    else upper[code - 65] = true;
  }
  let count = 0;
  for (let index = 0; index < 26; index++) {
    if (lower[index] && upper[index]) count++;
  }
  return count;
}

const numberOfSpecialChars = solve;
class Solution {
  numberOfSpecialChars(word) { return solve(word); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfSpecialChars };
