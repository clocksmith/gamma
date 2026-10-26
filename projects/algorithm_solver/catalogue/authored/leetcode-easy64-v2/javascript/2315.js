'use strict';

// 2315. Count Asterisks (Easy).
// Specification: https://leetcode.com/problems/count-asterisks/description/
// O(n) time, O(1) space; ignore asterisks inside paired vertical bars.
function solve(s) {
  let outside = true;
  let result = 0;
  for (const character of s) {
    if (character === '|') outside = !outside;
    else if (character === '*' && outside) result++;
  }
  return result;
}

const countAsterisks = solve;
class Solution {
  countAsterisks(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countAsterisks };
