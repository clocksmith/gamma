"use strict";
// Hack2Hire 6a04d7ad3141bbc31efdd5c2 (Minimum Machines for Task Scheduling) over an INFERRED spec; qualification unknown.

function solve(tasks) {
  const starts = Float64Array.from(tasks, (t) => t[0]).sort();
  const ends = Float64Array.from(tasks, (t) => t[1]).sort();
  let best = 0, j = 0;
  for (let i = 0; i < starts.length; i++) {
    while (ends[j] <= starts[i]) j++;
    if (i + 1 - j > best) best = i + 1 - j;
  }
  return best;
}

function minMachines(tasks) { return solve(tasks); }

module.exports = solve;
module.exports.minMachines = minMachines;
