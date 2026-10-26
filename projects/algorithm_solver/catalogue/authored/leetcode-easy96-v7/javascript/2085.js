'use strict';

// 2085. Count Common Words With One Occurrence (Easy).
// Specification: https://leetcode.com/problems/count-common-words-with-one-occurrence/description/
// O(total characters) expected time, O(n + m) map entries; preserve both lists.
function solve(words1, words2) {
  const first = new Map();
  const second = new Map();
  for (const word of words1) first.set(word, (first.get(word) || 0) + 1);
  for (const word of words2) second.set(word, (second.get(word) || 0) + 1);
  let total = 0;
  for (const [word, count] of first) {
    if (count === 1 && second.get(word) === 1) total++;
  }
  return total;
}

const countWords = solve;
class Solution {
  countWords(words1, words2) { return solve(words1, words2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countWords };
