'use strict';

// 3541. Find Most Frequent Vowel and Consonant (Easy).
// Specification: https://leetcode.com/problems/find-most-frequent-vowel-and-consonant/description/
// O(n) time, O(1) alphabet space; a missing vowel or consonant category contributes zero.
function solve(s) {
  const counts = new Array(26).fill(0);
  for (const character of s) counts[character.charCodeAt(0) - 97]++;
  const vowels = new Set([0, 4, 8, 14, 20]);
  let vowelMaximum = 0;
  let consonantMaximum = 0;
  for (let index = 0; index < counts.length; index++) {
    if (vowels.has(index)) vowelMaximum = Math.max(vowelMaximum, counts[index]);
    else consonantMaximum = Math.max(consonantMaximum, counts[index]);
  }
  return vowelMaximum + consonantMaximum;
}

const maxFreqSum = solve;
class Solution {
  maxFreqSum(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxFreqSum };
