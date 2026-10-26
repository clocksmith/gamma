'use strict';

// 2255. Count Prefixes of a Given String (Easy).
// Specification: https://leetcode.com/problems/count-prefixes-of-a-given-string/description/
// O(total word characters) time, O(1) auxiliary space; preserve words.
function solve(words, s) {
  let result = 0;
  for (const word of words) {
    if (s.startsWith(word)) result++;
  }
  return result;
}

const countPrefixes = solve;
class Solution {
  countPrefixes(words, s) { return solve(words, s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPrefixes };
