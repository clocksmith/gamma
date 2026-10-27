'use strict';

// 524. Longest Word in Dictionary through Deleting.

function solve(s, dictionary) {
  const ordered = dictionary.slice().sort((a, b) => b.length - a.length || (a < b ? -1 : a > b ? 1 : 0));
  for (const word of ordered) {
    let index = 0;
    for (const char of s) if (index < word.length && char === word[index]) index += 1;
    if (index === word.length) return word;
  }
  return '';
}

const findLongestWord = solve;
class Solution {
  findLongestWord(s, dictionary) { return solve(s, dictionary); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLongestWord };
