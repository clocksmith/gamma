'use strict';

// 884. Uncommon Words from Two Sentences (Easy).
// Specification: https://leetcode.com/problems/uncommon-words-from-two-sentences/description/
// O(L) expected time and O(L) space for total text length L; preserve inputs.
function solve(s1, s2) {
  const counts = new Map();
  for (const sentence of [s1, s2]) {
    for (const word of sentence.split(' ')) {
      if (word.length > 0) counts.set(word, (counts.get(word) || 0) + 1);
    }
  }
  const result = [];
  for (const [word, count] of counts) {
    if (count === 1) result.push(word);
  }
  return result;
}

const uncommonFromSentences = solve;
class Solution {
  uncommonFromSentences(s1, s2) { return solve(s1, s2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, uncommonFromSentences };
