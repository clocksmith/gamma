'use strict';

// 2506. Count Pairs Of Similar Strings (Easy).
// Specification: https://leetcode.com/problems/count-pairs-of-similar-strings/description/
// O(total characters) expected time, O(u) space. Masks use only bits 0-25.
function solve(words) {
  const counts = new Map();
  let result = 0;
  for (const word of words) {
    let mask = 0;
    for (const character of word) mask |= 1 << (character.charCodeAt(0) - 97);
    const previous = counts.get(mask) || 0;
    result += previous;
    counts.set(mask, previous + 1);
  }
  return result;
}

const similarPairs = solve;
class Solution {
  similarPairs(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, similarPairs };
