'use strict';

// 650. 2 Keys Keyboard (Medium).
// Specification: https://leetcode.com/problems/2-keys-keyboard/description/
function solve(n) {
  let steps = 0; let value = n; let divisor = 2;
  while (value > 1) {
    while (value % divisor === 0) { steps += divisor; value = Math.floor(value / divisor); }
    divisor++;
  }
  return steps;
}
const minSteps = solve;
class Solution { minSteps(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSteps };
