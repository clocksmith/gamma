'use strict';

// 1119. Remove Vowels from a String (Easy).
// Specification: https://leetcode.com/problems/remove-vowels-from-a-string/description/
// O(n) time and space; remove lowercase English vowels while preserving order.
function solve(s) {
  const vowels = new Set('aeiou');
  const result = [];
  for (const character of s) {
    if (!vowels.has(character)) result.push(character);
  }
  return result.join('');
}

const removeVowels = solve;
class Solution {
  removeVowels(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeVowels };
