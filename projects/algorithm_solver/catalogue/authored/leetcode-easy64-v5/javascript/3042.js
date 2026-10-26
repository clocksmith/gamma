'use strict';

// 3042. Count Prefix and Suffix Pairs I (Easy).
// Specification: https://leetcode.com/problems/count-prefix-and-suffix-pairs-i/description/
// O(n^2 * m) time, O(1) auxiliary space; m is maximum word length; preserve words.
function solve(words) {
  let pairs = 0;
  for (let left = 0; left < words.length; left++) {
    for (let right = left + 1; right < words.length; right++) {
      if (words[right].startsWith(words[left]) && words[right].endsWith(words[left])) pairs++;
    }
  }
  return pairs;
}

const countPrefixSuffixPairs = solve;
class Solution {
  countPrefixSuffixPairs(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPrefixSuffixPairs };
