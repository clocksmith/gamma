'use strict';

// 1510. Stone Game IV: winning-state dynamic programming; O(n*sqrt(n)) time and O(n) space.

function solve(n) {
  const winning = Array(n + 1).fill(false);
  for (let stones = 1; stones <= n; stones += 1) {
    for (let root = 1; root * root <= stones; root += 1) {
      if (!winning[stones - root * root]) {
        winning[stones] = true;
        break;
      }
    }
  }
  return winning[n];
}

const winnerSquareGame = solve;
class Solution {
  winnerSquareGame(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, winnerSquareGame };
