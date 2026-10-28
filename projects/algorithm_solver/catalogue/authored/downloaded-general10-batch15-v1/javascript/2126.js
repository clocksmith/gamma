'use strict';

// 2126. Destroying Asteroids (Medium).
// Specification: https://leetcode.com/problems/destroying-asteroids/description/
function solve(mass, asteroids) {
  const sorted = asteroids.slice().sort((a, b) => a - b);
  for (const asteroid of sorted) {
    if (mass < asteroid) return false;
    mass += asteroid;
  }
  return true;
}
const asteroidsDestroyed = solve;
class Solution { asteroidsDestroyed(mass, asteroids) { return solve(mass, asteroids); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, asteroidsDestroyed };
