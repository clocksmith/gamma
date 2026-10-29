"use strict";
// Hack2Hire 69c7f82d21f6ab4226966a80 (Fuel Station Queue Simulation) over an INFERRED spec; qualification unknown.

function solve(demands, x, y, z) {
  const fuel = [x, y, z], freeAt = [0, 0, 0];
  let previousStart = 0, worst = 0;
  for (const demand of demands) {
    let start = -1;
    for (let i = 0; i < 3; i++) {
      if (fuel[i] >= demand) {
        const s = Math.max(previousStart, freeAt[i]);
        if (start < 0 || s < start) start = s;
      }
    }
    if (start < 0) return -1; // fuel only decreases, so this car can never be served
    let chosen = 0;
    while (fuel[chosen] < demand || freeAt[chosen] > start) chosen++;
    fuel[chosen] -= demand;
    freeAt[chosen] = start + demand;
    previousStart = start;
    if (start > worst) worst = start;
  }
  return worst;
}

function maxWaitingTime(demands, x, y, z) { return solve(demands, x, y, z); }

module.exports = solve;
module.exports.maxWaitingTime = maxWaitingTime;
