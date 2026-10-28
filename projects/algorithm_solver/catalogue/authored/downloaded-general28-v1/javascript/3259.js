'use strict';

// 3259. Maximum Energy Boost From Two Drinks (Medium).
// Specification: https://leetcode.com/problems/maximum-energy-boost-from-two-drinks/description/
function solve(energyDrinkA, energyDrinkB) {
  const n = energyDrinkA.length;
  let a = energyDrinkA[0]; let b = energyDrinkB[0]; let c = 0;
  for (let i = 1; i < n; i++) {
    const na = energyDrinkA[i] + Math.max(a, c);
    const nb = energyDrinkB[i] + Math.max(b, c);
    const nc = Math.max(a, b, c);
    a = na; b = nb; c = nc;
  }
  return Math.max(a, b, c);
}
const maxEnergyBoost = solve;
class Solution { maxEnergyBoost(energyDrinkA, energyDrinkB) { return solve(energyDrinkA, energyDrinkB); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxEnergyBoost };
