'use strict';

// 2942. Find Words Containing Character (Easy).
// Specification: https://leetcode.com/problems/find-words-containing-character/description/
// O(total characters) time, O(1) auxiliary space excluding output; preserve word indices.
function solve(words, x) {
  const result = [];
  for (let index = 0; index < words.length; index++) {
    if (words[index].includes(x)) result.push(index);
  }
  return result;
}

const findWordsContaining = solve;
class Solution {
  findWordsContaining(words, x) { return solve(words, x); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findWordsContaining };
