'use strict';

// 390. Elimination Game (Medium).
// Specification: https://leetcode.com/problems/elimination-game/description/
function solve(n) {
  let head = 1; let step = 1; let remaining = n; let fromLeft = true;
  while (remaining > 1) {
    if (fromLeft || remaining % 2 === 1) head += step;
    remaining = Math.floor(remaining / 2);
    step *= 2;
    fromLeft = !fromLeft;
  }
  return head;
}
const lastRemaining = solve;
class Solution { lastRemaining(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, lastRemaining };
