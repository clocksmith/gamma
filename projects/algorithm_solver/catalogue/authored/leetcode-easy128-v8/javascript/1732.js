'use strict';

// 1732. Find the Highest Altitude (Easy).
// Specification: https://leetcode.com/problems/find-the-highest-altitude/description/
// O(n) time, O(1) space; include the initial altitude of zero among prefix sums.
function solve(gain) {
  let altitude = 0;
  let highest = 0;
  for (const change of gain) {
    altitude += change;
    highest = Math.max(highest, altitude);
  }
  return highest;
}

const largestAltitude = solve;
class Solution {
  largestAltitude(gain) { return solve(gain); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestAltitude };
