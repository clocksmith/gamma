'use strict';

// 319. Bulb Switcher (Medium).
// Specification: https://leetcode.com/problems/bulb-switcher/description/
function solve(n) {
  return Math.floor(Math.sqrt(n));
}
const bulbSwitch = solve;
class Solution { bulbSwitch(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, bulbSwitch };
