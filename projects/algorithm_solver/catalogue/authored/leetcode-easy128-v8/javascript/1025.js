'use strict';

// 1025. Divisor Game (Easy).
// Specification: https://leetcode.com/problems/divisor-game/description/
// O(1) time and space; even starting values are winning positions under optimal play.
function solve(n) {
  return n % 2 === 0;
}

const divisorGame = solve;
class Solution {
  divisorGame(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, divisorGame };
