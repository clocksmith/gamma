"use strict";
// Hack2Hire 6a0226e62608e589a944a229 (Fill Layover With Experiences) over an INFERRED spec; qualification unknown.

function solve(durations, totalHours) {
  const options = [...new Set(durations)].sort((a, b) => a - b);
  const unreachable = totalHours + 1;
  const best = new Array(totalHours + 1).fill(unreachable);
  best[0] = 0;
  for (let s = 1; s <= totalHours; s++) {
    let b = unreachable;
    for (const d of options) {
      if (d > s) break;
      const c = best[s - d] + 1;
      if (c < b) b = c;
    }
    best[s] = b;
  }
  return best[totalHours] <= totalHours ? best[totalHours] : -1;
}

function minBookings(durations, totalHours) { return solve(durations, totalHours); }

module.exports = solve;
module.exports.minBookings = minBookings;
