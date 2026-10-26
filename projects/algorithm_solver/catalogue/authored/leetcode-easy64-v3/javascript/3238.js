'use strict';

// 3238. Find the Number of Winning Players (Easy).
// Specification: https://leetcode.com/problems/find-the-number-of-winning-players/description/
// O(n + picks) time, O(n) space for the fixed eleven-color domain; preserve pick.
function solve(n, pick) {
  const counts = Array.from({ length: n }, () => new Array(11).fill(0));
  for (const [player, color] of pick) counts[player][color]++;
  let winners = 0;
  for (let player = 0; player < n; player++) {
    for (const count of counts[player]) {
      if (count > player) {
        winners++;
        break;
      }
    }
  }
  return winners;
}

const winningPlayerCount = solve;
class Solution {
  winningPlayerCount(n, pick) { return solve(n, pick); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, winningPlayerCount };
