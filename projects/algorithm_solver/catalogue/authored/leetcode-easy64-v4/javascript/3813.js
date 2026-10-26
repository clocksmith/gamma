'use strict';

// 3813. Vowel-Consonant Score (Easy).
// Specification: https://leetcode.com/problems/vowel-consonant-score/description/
// O(n) time, O(1) space; ignore spaces and digits, and return zero without consonants.
function solve(s) {
  let vowels = 0;
  let consonants = 0;
  for (const character of s) {
    if ('aeiou'.includes(character)) vowels++;
    else if (character >= 'a' && character <= 'z') consonants++;
  }
  return consonants === 0 ? 0 : Math.floor(vowels / consonants);
}

const vowelConsonantScore = solve;
class Solution {
  vowelConsonantScore(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, vowelConsonantScore };
