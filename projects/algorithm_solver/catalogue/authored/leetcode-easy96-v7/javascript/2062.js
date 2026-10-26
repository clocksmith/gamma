'use strict';

// 2062. Count Vowel Substrings of a String (Easy).
// Specification: https://leetcode.com/problems/count-vowel-substrings-of-a-string/description/
// O(n) time, O(1) space; count valid starts after the latest consonant from vowel last positions.
function solve(word) {
  const vowels = 'aeiou';
  const latest = new Array(5).fill(-1);
  let boundary = -1;
  let total = 0;
  for (let index = 0; index < word.length; index++) {
    const vowel = vowels.indexOf(word[index]);
    if (vowel < 0) {
      boundary = index;
      continue;
    }
    latest[vowel] = index;
    let earliest = latest[0];
    for (let offset = 1; offset < latest.length; offset++) {
      earliest = Math.min(earliest, latest[offset]);
    }
    total += Math.max(0, earliest - boundary);
  }
  return total;
}

const countVowelSubstrings = solve;
class Solution {
  countVowelSubstrings(word) { return solve(word); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countVowelSubstrings };
