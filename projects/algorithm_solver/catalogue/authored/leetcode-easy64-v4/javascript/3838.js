'use strict';

// 3838. Weighted Word Mapping (Easy).
// Specification: https://leetcode.com/problems/weighted-word-mapping/description/
// O(total characters) time, O(word count) output space; preserve words and weights.
function solve(words, weights) {
  const result = [];
  for (const word of words) {
    let weight = 0;
    for (const character of word) weight += weights[character.charCodeAt(0) - 97];
    result.push(String.fromCharCode(122 - weight % 26));
  }
  return result.join('');
}

const mapWordWeights = solve;
class Solution {
  mapWordWeights(words, weights) { return solve(words, weights); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mapWordWeights };
