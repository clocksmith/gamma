'use strict';

// 2114. Maximum Number of Words Found in Sentences (Easy).
// Specification: https://leetcode.com/problems/maximum-number-of-words-found-in-sentences/description/
// O(total characters) time, O(1) space; count single-space word separators; preserve sentences.
function solve(sentences) {
  let maximum = 0;
  for (const sentence of sentences) {
    let words = 1;
    for (const character of sentence) {
      if (character === ' ') words++;
    }
    maximum = Math.max(maximum, words);
  }
  return maximum;
}

const mostWordsFound = solve;
class Solution {
  mostWordsFound(sentences) { return solve(sentences); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mostWordsFound };
