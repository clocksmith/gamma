'use strict';

// 1180. Count Substrings with Only One Distinct Letter (Easy).
// Specification: https://leetcode.com/problems/count-substrings-with-only-one-distinct-letter/description/
// O(n) time, O(1) space; the current equal-character run counts substrings ending here.
function solve(s) {
  let run = 0;
  let total = 0;
  for (let index = 0; index < s.length; index++) {
    run = index > 0 && s[index] === s[index - 1] ? run + 1 : 1;
    total += run;
  }
  return total;
}

const countLetters = solve;
class Solution {
  countLetters(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countLetters };
