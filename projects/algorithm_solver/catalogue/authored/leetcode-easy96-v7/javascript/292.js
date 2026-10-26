'use strict';

// 292. Nim Game (Easy).
// Specification: https://leetcode.com/problems/nim-game/description/
// O(1) time and space; multiples of four are losing positions.
function solve(n) {
  return n % 4 !== 0;
}

const canWinNim = solve;
class Solution {
  canWinNim(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canWinNim };
