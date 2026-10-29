"use strict";
// Hack2Hire 68f6f36986f7cb4953d40fbc (Game Machine) over an INFERRED spec; qualification unknown.

function solve(energyCosts, points, initialEnergy) {
  const n = energyCosts.length;
  let end = 0, cost = 0, score = 0, best = null;
  for (let start = 0; start < n; start++) {
    if (end < start) { end = start; cost = 0; score = 0; }
    while (end < n && cost + energyCosts[end] <= initialEnergy) { cost += energyCosts[end]; score += points[end]; end++; }
    if (best === null || score > best) best = score;
    if (end > start) { cost -= energyCosts[start]; score -= points[start]; }
  }
  return best;
}

function maxGamePoints(energyCosts, points, initialEnergy) { return solve(energyCosts, points, initialEnergy); }

module.exports = solve;
module.exports.maxGamePoints = maxGamePoints;
