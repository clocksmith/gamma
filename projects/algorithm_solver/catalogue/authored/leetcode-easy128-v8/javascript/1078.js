'use strict';

// 1078. Occurrences After Bigram (Easy).
// Specification: https://leetcode.com/problems/occurrences-after-bigram/description/
// O(total characters) time and space; preserve encounter order and overlapping bigrams.
function solve(text, first, second) {
  const words = text.split(' ');
  const result = [];
  for (let index = 2; index < words.length; index++) {
    if (words[index - 2] === first && words[index - 1] === second) result.push(words[index]);
  }
  return result;
}

const findOcurrences = solve;
class Solution {
  findOcurrences(text, first, second) { return solve(text, first, second); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findOcurrences };
