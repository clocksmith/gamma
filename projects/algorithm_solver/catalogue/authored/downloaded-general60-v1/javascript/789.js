'use strict';

// 789. Escape The Ghosts (Medium).
// Specification: https://leetcode.com/problems/escape-the-ghosts/description/
function solve(ghosts, target) {
  const player = Math.abs(target[0]) + Math.abs(target[1]);
  for (const [gx, gy] of ghosts) {
    if (Math.abs(gx - target[0]) + Math.abs(gy - target[1]) <= player) return false;
  }
  return true;
}
const escapeGhosts = solve;
class Solution { escapeGhosts(ghosts, target) { return solve(ghosts, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, escapeGhosts };
