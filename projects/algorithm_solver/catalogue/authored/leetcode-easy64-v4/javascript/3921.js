'use strict';

// 3921. Score Validator (Easy).
// Specification: https://leetcode.com/problems/score-validator/description/
// O(n) time, O(1) space; stop immediately after the tenth wicket and preserve events.
function solve(events) {
  let score = 0;
  let wickets = 0;
  for (const event of events) {
    if (event === 'W') {
      wickets++;
      if (wickets === 10) break;
    } else if (event === 'WD' || event === 'NB') {
      score++;
    } else {
      score += Number(event);
    }
  }
  return [score, wickets];
}

const scoreValidator = solve;
class Solution {
  scoreValidator(events) { return solve(events); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, scoreValidator };
