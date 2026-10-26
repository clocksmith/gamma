'use strict';

// 1859. Sorting the Sentence (Easy).
// Specification: https://leetcode.com/problems/sorting-the-sentence/description/
// O(n) time, O(n) space; at most nine words with unique trailing positions.
function solve(s) {
  const words = s.split(' ');
  const ordered = new Array(words.length);
  for (const word of words) {
    const position = Number(word[word.length - 1]) - 1;
    ordered[position] = word.slice(0, -1);
  }
  return ordered.join(' ');
}

const sortSentence = solve;
class Solution {
  sortSentence(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sortSentence };
