'use strict';

// 1839. Longest Substring Of All Vowels in Order: track nondecreasing vowel runs containing all five distinct vowels.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(word) {
  let best = 0;
  let run = 0;
  let distinct = 0;
  let previous = '';
  for (const vowel of word) {
    if (previous === '' || vowel < previous) {
      run = 1;
      distinct = 1;
    } else {
      run += 1;
      if (vowel > previous) distinct += 1;
    }
    if (distinct === 5) best = Math.max(best, run);
    previous = vowel;
  }
  return best;
}

const longestBeautifulSubstring = solve;
class Solution {
  longestBeautifulSubstring(word) { return solve(word); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestBeautifulSubstring };
