"use strict";
// Hack2Hire 68e9554c149617c9114ecdd1 (Racing Points and Winner, variant 2) over an INFERRED spec; qualification unknown.

const POINTS = [15, 10, 5];

function solve(races) {
  const stats = new Map(); // rider -> [points, firsts, seconds, thirds]
  for (const race of races) {
    race.forEach((rider, pos) => {
      let row = stats.get(rider);
      if (!row) stats.set(rider, row = [0, 0, 0, 0]);
      if (pos < 3) { row[0] += POINTS[pos]; row[pos + 1] += 1; }
    });
  }
  return [...stats.keys()].sort((a, b) => {
    const x = stats.get(a), y = stats.get(b);
    for (let i = 0; i < 4; i++) if (x[i] !== y[i]) return y[i] - x[i];
    return a < b ? -1 : a > b ? 1 : 0;
  });
}

function seasonStandings(races) { return solve(races); }

module.exports = solve;
module.exports.seasonStandings = seasonStandings;
