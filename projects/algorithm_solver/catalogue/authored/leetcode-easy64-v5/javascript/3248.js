'use strict';

// 3248. Snake in Matrix (Easy).
// Specification: https://leetcode.com/problems/snake-in-matrix/description/
// O(number of commands) time, O(1) space; input commands are guaranteed to stay in bounds.
function solve(n, commands) {
  let position = 0;
  for (const command of commands) {
    if (command === 'UP') position -= n;
    else if (command === 'DOWN') position += n;
    else if (command === 'LEFT') position--;
    else if (command === 'RIGHT') position++;
  }
  return position;
}

const finalPositionOfSnake = solve;
class Solution {
  finalPositionOfSnake(n, commands) { return solve(n, commands); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, finalPositionOfSnake };
