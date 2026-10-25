'use strict';

// 2383. Minimum Hours of Training to Win a Competition (Easy).
// Specification: https://leetcode.com/problems/minimum-hours-of-training-to-win-a-competition/description/
// O(n) time, O(1) auxiliary space. Training must make both stats strictly greater.
function solve(initialEnergy, initialExperience, energy, experience) {
  let totalEnergy = 0;
  for (const required of energy) totalEnergy += required;
  let hours = Math.max(0, totalEnergy + 1 - initialEnergy);
  let currentExperience = initialExperience;
  for (const required of experience) {
    if (currentExperience <= required) {
      const extra = required + 1 - currentExperience;
      hours += extra;
      currentExperience += extra;
    }
    currentExperience += required;
  }
  return hours;
}

const minNumberOfHours = solve;
class Solution {
  minNumberOfHours(initialEnergy, initialExperience, energy, experience) { return solve(initialEnergy, initialExperience, energy, experience); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minNumberOfHours };
