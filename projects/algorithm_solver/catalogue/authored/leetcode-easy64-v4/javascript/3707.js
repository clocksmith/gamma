'use strict';

// 3707. Equal Score Substrings (Easy).
// Specification: https://leetcode.com/problems/equal-score-substrings/description/
// O(n) time, O(1) space; require two nonempty substrings.
function solve(s) {
  let total = 0;
  for (const character of s) total += character.charCodeAt(0) - 96;
  let leftScore = 0;
  for (let index = 0; index < s.length - 1; index++) {
    leftScore += s.charCodeAt(index) - 96;
    if (leftScore * 2 === total) return true;
  }
  return false;
}

const scoreBalance = solve;
class Solution {
  scoreBalance(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, scoreBalance };
