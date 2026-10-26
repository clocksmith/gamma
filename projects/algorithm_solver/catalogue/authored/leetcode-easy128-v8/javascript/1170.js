'use strict';

// 1170. Compare Strings by Frequency of the Smallest Character (Easy).
// Specification: https://leetcode.com/problems/compare-strings-by-frequency-of-the-smallest-character/description/
// O(L + w log w + q log w) time, O(w + q) space; upper-bound search counts strictly greater frequencies.
function solve(queries, words) {
  function frequency(text) {
    let smallest = '{';
    let count = 0;
    for (const character of text) {
      if (character < smallest) {
        smallest = character;
        count = 1;
      } else if (character === smallest) {
        count++;
      }
    }
    return count;
  }
  const frequencies = words.map(frequency).sort((a, b) => a - b);
  return queries.map(query => {
    const target = frequency(query);
    let left = 0;
    let right = frequencies.length;
    while (left < right) {
      const middle = left + Math.floor((right - left) / 2);
      if (frequencies[middle] <= target) left = middle + 1;
      else right = middle;
    }
    return frequencies.length - left;
  });
}

const numSmallerByFrequency = solve;
class Solution {
  numSmallerByFrequency(queries, words) { return solve(queries, words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numSmallerByFrequency };
