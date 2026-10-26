'use strict';

// 3360. Stone Removal Game (Easy).
// Specification: https://leetcode.com/problems/stone-removal-game/description/
// O(1) time and space under 1 <= n <= 50; count successful alternating moves.
function solve(n) {
  let removal = 10;
  let aliceWins = false;
  while (removal > 0 && n >= removal) {
    n -= removal;
    removal--;
    aliceWins = !aliceWins;
  }
  return aliceWins;
}

const canAliceWin = solve;
class Solution {
  canAliceWin(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canAliceWin };
