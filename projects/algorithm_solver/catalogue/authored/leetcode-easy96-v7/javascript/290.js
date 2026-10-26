'use strict';

// 290. Word Pattern (Easy).
// Specification: https://leetcode.com/problems/word-pattern/description/
// O(n + m) time and space for the input text; require a character-to-word bijection.
function solve(pattern, s) {
  const words = s.split(' ');
  if (words.length !== pattern.length) return false;
  const forward = new Map();
  const backward = new Map();
  for (let index = 0; index < words.length; index++) {
    const character = pattern[index];
    const word = words[index];
    if (forward.has(character) && forward.get(character) !== word) return false;
    if (backward.has(word) && backward.get(word) !== character) return false;
    forward.set(character, word);
    backward.set(word, character);
  }
  return true;
}

const wordPattern = solve;
class Solution {
  wordPattern(pattern, s) { return solve(pattern, s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, wordPattern };
