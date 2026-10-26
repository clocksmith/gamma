'use strict';

// 2068. Check Whether Two Strings are Almost Equivalent (Easy).
// Specification: https://leetcode.com/problems/check-whether-two-strings-are-almost-equivalent/description/
// O(n + m) time, O(1) space for 26 lowercase letters; every frequency difference is at most three.
function solve(word1, word2) {
  const difference = new Array(26).fill(0);
  for (const character of word1) difference[character.charCodeAt(0) - 97]++;
  for (const character of word2) difference[character.charCodeAt(0) - 97]--;
  return difference.every(count => Math.abs(count) <= 3);
}

const checkAlmostEquivalent = solve;
class Solution {
  checkAlmostEquivalent(word1, word2) { return solve(word1, word2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkAlmostEquivalent };
