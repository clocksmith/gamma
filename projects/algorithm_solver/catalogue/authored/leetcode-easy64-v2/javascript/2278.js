'use strict';

// 2278. Percentage of Letter in String (Easy).
// Specification: https://leetcode.com/problems/percentage-of-letter-in-string/description/
// O(n) time, O(1) space; round the nonnegative percentage down.
function solve(s, letter) {
  let count = 0;
  for (const character of s) {
    if (character === letter) count++;
  }
  return Math.floor(100 * count / s.length);
}

const percentageLetter = solve;
class Solution {
  percentageLetter(s, letter) { return solve(s, letter); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, percentageLetter };
