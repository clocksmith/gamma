'use strict';

// 1823. Find the Winner of the Circular Game (Medium).
// Specification: https://leetcode.com/problems/find-the-winner-of-the-circular-game/description/
function solve(n, k) {
  let winner = 0;
  for (let people = 2; people <= n; people++) winner = (winner + k) % people;
  return winner + 1;
}
const findTheWinner = solve;
class Solution { findTheWinner(n, k) { return solve(n, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findTheWinner };
