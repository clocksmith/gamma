"use strict";
// Hack2Hire 69b78e4e8a0eeb9897a8d2a5 (Garage Occupancy per Timestamp) over an INFERRED spec; qualification unknown.

function solve(n, tickets) {
  const change = new Array(n + 1).fill(0);
  for (const [entry, leave] of tickets) {
    change[entry]++;
    change[leave + 1]--;
  }
  const result = [];
  let current = 0;
  for (let t = 0; t < n; t++) {
    current += change[t];
    result.push(current);
  }
  return result;
}

function getOccupancy(n, tickets) { return solve(n, tickets); }

module.exports = solve;
module.exports.getOccupancy = getOccupancy;
