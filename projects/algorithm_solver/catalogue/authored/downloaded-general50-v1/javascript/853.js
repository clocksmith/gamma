'use strict';

// 853. Car Fleet (Medium).
// Specification: https://leetcode.com/problems/car-fleet/description/
function solve(target, position, speed) {
  const cars = position.map((p, i) => [p, speed[i]]).sort((a, b) => b[0] - a[0]);
  let fleets = 0; let slowest = -1;
  for (const [p, s] of cars) {
    const time = (target - p) / s;
    if (time > slowest) { fleets++; slowest = time; }
  }
  return fleets;
}
const carFleet = solve;
class Solution { carFleet(target, position, speed) { return solve(target, position, speed); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, carFleet };
