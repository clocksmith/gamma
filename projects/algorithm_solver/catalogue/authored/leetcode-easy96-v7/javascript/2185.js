'use strict';

// 2185. Counting Words With a Given Prefix (Easy).
// Specification: https://leetcode.com/problems/counting-words-with-a-given-prefix/description/
// O(n * p) time for n words and prefix length p, O(1) auxiliary space; preserve words.
function solve(words, pref) {
  let count = 0;
  for (const word of words) {
    if (word.startsWith(pref)) count++;
  }
  return count;
}

const prefixCount = solve;
class Solution {
  prefixCount(words, pref) { return solve(words, pref); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, prefixCount };
