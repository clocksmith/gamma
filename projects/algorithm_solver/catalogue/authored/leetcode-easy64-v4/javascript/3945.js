'use strict';

// 3945. Digit Frequency Score (Easy).
// Specification: https://leetcode.com/problems/digit-frequency-score/description/
// O(d) time, O(1) space; summing each digit once equals the frequency-weighted score.
function solve(n) {
  let remaining = n;
  let score = 0;
  while (remaining > 0) {
    score += remaining % 10;
    remaining = Math.floor(remaining / 10);
  }
  return score;
}

const digitFrequencyScore = solve;
class Solution {
  digitFrequencyScore(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, digitFrequencyScore };
