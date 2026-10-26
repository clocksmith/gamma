'use strict';

// 3222. Find the Winning Player in Coin Game (Easy).
// Specification: https://leetcode.com/problems/find-the-winning-player-in-coin-game/description/
// O(1) time and space; each legal turn consumes one 75-value and four 10-value coins.
function solve(x, y) {
  const turns = Math.min(x, Math.floor(y / 4));
  return turns % 2 === 1 ? 'Alice' : 'Bob';
}

const losingPlayer = solve;
class Solution {
  losingPlayer(x, y) { return solve(x, y); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, losingPlayer };
