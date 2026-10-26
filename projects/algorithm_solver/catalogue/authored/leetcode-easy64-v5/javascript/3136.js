'use strict';

// 3136. Valid Word (Easy).
// Specification: https://leetcode.com/problems/valid-word/description/
// O(n) time, O(1) auxiliary space; accept ASCII letters/digits only, with a vowel and consonant.
function solve(word) {
  if (word.length < 3) return false;
  let hasVowel = false;
  let hasConsonant = false;
  for (const character of word) {
    if (character >= '0' && character <= '9') continue;
    const lower = character.toLowerCase();
    if (lower < 'a' || lower > 'z') return false;
    if ('aeiou'.includes(lower)) hasVowel = true;
    else hasConsonant = true;
  }
  return hasVowel && hasConsonant;
}

const isValid = solve;
class Solution {
  isValid(word) { return solve(word); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isValid };
