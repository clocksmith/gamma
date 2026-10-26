'use strict';

// 657. Robot Return to Origin (Easy).
// Specification: https://leetcode.com/problems/robot-return-to-origin/description/
// O(n) time, O(1) space; accumulate horizontal and vertical displacement.
function solve(moves) {
  let horizontal = 0;
  let vertical = 0;
  for (const move of moves) {
    if (move === 'L') horizontal--;
    else if (move === 'R') horizontal++;
    else if (move === 'U') vertical++;
    else vertical--;
  }
  return horizontal === 0 && vertical === 0;
}

const judgeCircle = solve;
class Solution {
  judgeCircle(moves) { return solve(moves); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, judgeCircle };
