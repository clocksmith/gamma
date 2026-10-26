'use strict';

// 1065. Index Pairs of a String (Easy).
// Specification: https://leetcode.com/problems/index-pairs-of-a-string/description/
// O(n * totalWordLength + p log p) time, O(p) output space; report all overlapping matches.
function solve(text, words) {
  const result = [];
  for (let start = 0; start < text.length; start++) {
    for (const word of words) {
      if (text.startsWith(word, start)) result.push([start, start + word.length - 1]);
    }
  }
  result.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  return result;
}

const indexPairs = solve;
class Solution {
  indexPairs(text, words) { return solve(text, words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, indexPairs };
