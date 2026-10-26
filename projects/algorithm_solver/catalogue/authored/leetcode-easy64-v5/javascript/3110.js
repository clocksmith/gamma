'use strict';

// 3110. Score of a String (Easy).
// Specification: https://leetcode.com/problems/score-of-a-string/description/
// O(n) time, O(1) auxiliary space; the input alphabet is lowercase English.
function solve(s) {
  let score = 0;
  for (let index = 1; index < s.length; index++) {
    score += Math.abs(s.charCodeAt(index) - s.charCodeAt(index - 1));
  }
  return score;
}

const scoreOfString = solve;
class Solution {
  scoreOfString(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, scoreOfString };
