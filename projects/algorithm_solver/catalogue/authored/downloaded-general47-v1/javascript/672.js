'use strict';

// 672. Bulb Switcher II (Medium).
// Specification: https://leetcode.com/problems/bulb-switcher-ii/description/
function solve(n, presses) {
  if (presses === 0) return 1;
  if (n === 1) return 2;
  if (n === 2) return presses === 1 ? 3 : 4;
  if (presses === 1) return 4;
  if (presses === 2) return 7;
  return 8;
}
const flipLights = solve;
class Solution { flipLights(n, presses) { return solve(n, presses); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, flipLights };
