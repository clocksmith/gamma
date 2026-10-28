'use strict';

// 754. Reach a Number (Medium).
// Specification: https://leetcode.com/problems/reach-a-number/description/
function solve(target) {
  const goal = Math.abs(target);
  let steps = 0; let total = 0;
  while (total < goal || (total - goal) % 2 !== 0) { steps++; total += steps; }
  return steps;
}
const reachNumber = solve;
class Solution { reachNumber(target) { return solve(target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reachNumber };
