'use strict';

// 1446. Consecutive Characters (Easy).
// Specification: https://leetcode.com/problems/consecutive-characters/description/
// O(n) time, O(1) space; track the longest equal-character run.
function solve(s) {
  let longest = 0;
  let length = 0;
  let previous = '';
  for (const character of s) {
    length = character === previous ? length + 1 : 1;
    previous = character;
    longest = Math.max(longest, length);
  }
  return longest;
}

const maxPower = solve;
class Solution {
  maxPower(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxPower };
