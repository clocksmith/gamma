'use strict';

// 2490. Circular Sentence (Easy).
// Specification: https://leetcode.com/problems/circular-sentence/description/
// O(n) time, O(1) space; valid words are separated by single spaces.
function solve(sentence) {
  if (sentence[0] !== sentence[sentence.length - 1]) return false;
  for (let index = 1; index < sentence.length - 1; index++) {
    if (sentence[index] === ' ' && sentence[index - 1] !== sentence[index + 1]) return false;
  }
  return true;
}

const isCircularSentence = solve;
class Solution {
  isCircularSentence(sentence) { return solve(sentence); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isCircularSentence };
