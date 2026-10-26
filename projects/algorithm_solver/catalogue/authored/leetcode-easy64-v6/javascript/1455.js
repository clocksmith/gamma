'use strict';

// 1455. Check If a Word Occurs As a Prefix of Any Word in a Sentence (Easy).
// Specification: https://leetcode.com/problems/check-if-a-word-occurs-as-a-prefix-of-any-word-in-a-sentence/description/
// O(len(sentence) + len(searchWord)) time, O(len(sentence)) space; return a one-based index.
function solve(sentence, searchWord) {
  const words = sentence.split(' ');
  for (let index = 0; index < words.length; index++) {
    if (words[index].startsWith(searchWord)) return index + 1;
  }
  return -1;
}

const isPrefixOfWord = solve;
class Solution {
  isPrefixOfWord(sentence, searchWord) { return solve(sentence, searchWord); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isPrefixOfWord };
