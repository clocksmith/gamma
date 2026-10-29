"use strict";
// Hack2Hire 68e8779c80f69c7a01706899 (Racing Points and Winner, variant 1) over an INFERRED spec; qualification unknown.

const POINTS = [15, 10, 5];

function solve(races) {
  const total = new Map();
  for (const race of races) {
    race.forEach((rider, pos) => total.set(rider, (total.get(rider) || 0) + (pos < 3 ? POINTS[pos] : 0)));
  }
  let bestName = null, bestPoints = -1;
  for (const [rider, points] of total) {
    if (points > bestPoints || (points === bestPoints && rider < bestName)) { bestName = rider; bestPoints = points; }
  }
  return bestName;
}

function seasonWinner(races) { return solve(races); }

module.exports = solve;
module.exports.seasonWinner = seasonWinner;
