'use strict';

// 1408. String Matching in an Array (Easy).
// Specification: https://leetcode.com/problems/string-matching-in-an-array/description/
// O(n^2 * L^2) conservative substring-search time, O(n) result space; preserve words.
function solve(words) {
  const result = [];
  for (let index = 0; index < words.length; index++) {
    for (let other = 0; other < words.length; other++) {
      if (index !== other && words[other].includes(words[index])) {
        result.push(words[index]);
        break;
      }
    }
  }
  return result;
}

const stringMatching = solve;
class Solution {
  stringMatching(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, stringMatching };
