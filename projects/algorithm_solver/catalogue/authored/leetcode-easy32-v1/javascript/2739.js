'use strict';

// 2739. Total Distance Traveled (Easy).
// Specification: https://leetcode.com/problems/total-distance-traveled/description/
// O(1) time and space. Each transfer consumes a net four liters from the main tank.
function solve(mainTank, additionalTank) {
  const transfers = Math.min(additionalTank, Math.floor((mainTank - 1) / 4));
  return 10 * (mainTank + transfers);
}

const distanceTraveled = solve;
class Solution {
  distanceTraveled(mainTank, additionalTank) { return solve(mainTank, additionalTank); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, distanceTraveled };
