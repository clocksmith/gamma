'use strict';

// 2788. Split Strings by Separator (Easy).
// Specification: https://leetcode.com/problems/split-strings-by-separator/description/
// O(total characters) time and space; preserve input order and omit empty pieces.
function solve(words, separator) {
  const result = [];
  for (const word of words) {
    for (const part of word.split(separator)) {
      if (part.length > 0) result.push(part);
    }
  }
  return result;
}

const splitWordsBySeparator = solve;
class Solution {
  splitWordsBySeparator(words, separator) { return solve(words, separator); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, splitWordsBySeparator };
