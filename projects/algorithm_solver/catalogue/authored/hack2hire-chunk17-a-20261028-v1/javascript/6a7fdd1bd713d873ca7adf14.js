"use strict";
// Hack2Hire 6a7fdd1bd713d873ca7adf14 (Scooter Street Simulation) over an INFERRED spec; qualification unknown.

function solve(finish, scooters) {
  const positions = Float64Array.from(scooters.filter((p) => p < finish)).sort();
  let covered = 0, reach = 0;
  for (const s of positions) {
    const end = Math.min(s + 10, finish);
    if (end > reach) {
      covered += end - Math.max(s, reach);
      reach = end;
    }
  }
  return finish - covered;
}

function minWalkingDistance(finish, scooters) { return solve(finish, scooters); }

module.exports = solve;
module.exports.minWalkingDistance = minWalkingDistance;
