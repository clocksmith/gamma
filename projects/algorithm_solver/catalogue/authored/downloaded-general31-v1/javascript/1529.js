'use strict';

// 1529. Bulb Switcher IV (Medium).
// Specification: https://leetcode.com/problems/bulb-switcher-iv/description/
function solve(target) {
  let flips = 0;
  let current = '0';
  for (const ch of target) {
    if (ch !== current) { flips++; current = ch; }
  }
  return flips;
}
const minFlips = solve;
class Solution { minFlips(target) { return solve(target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minFlips };
