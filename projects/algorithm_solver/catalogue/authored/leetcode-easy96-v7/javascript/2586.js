'use strict';

// 2586. Count the Number of Vowel Strings in Range (Easy).
// Specification: https://leetcode.com/problems/count-the-number-of-vowel-strings-in-range/description/
// O(right - left + 1) time, O(1) space; both endpoints of each word must be vowels; preserve words.
function solve(words, left, right) {
  const vowels = 'aeiou';
  let count = 0;
  for (let index = left; index <= right; index++) {
    const word = words[index];
    if (vowels.includes(word[0]) && vowels.includes(word[word.length - 1])) count++;
  }
  return count;
}

const vowelStrings = solve;
class Solution {
  vowelStrings(words, left, right) { return solve(words, left, right); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, vowelStrings };
