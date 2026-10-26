'use strict';

// 824. Goat Latin (Easy).
// Specification: https://leetcode.com/problems/goat-latin/description/
// O(n + w^2) time and space including the required growing suffixes.
function solve(sentence) {
  const words = sentence.split(' ');
  const vowels = new Set('aeiouAEIOU');
  const result = [];
  for (let index = 0; index < words.length; index++) {
    const word = words[index];
    const stem = vowels.has(word[0]) ? word : word.slice(1) + word[0];
    result.push(stem + 'ma' + 'a'.repeat(index + 1));
  }
  return result.join(' ');
}

const toGoatLatin = solve;
class Solution {
  toGoatLatin(sentence) { return solve(sentence); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, toGoatLatin };
