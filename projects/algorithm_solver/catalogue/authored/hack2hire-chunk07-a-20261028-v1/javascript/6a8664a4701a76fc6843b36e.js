"use strict";
// Hack2Hire 6a8664a4701a76fc6843b36e (Maximum Testing Efficiency) over an INFERRED spec; qualification unknown.

function solve(arrivalTime) {
  const times = Float64Array.from(arrivalTime).sort();
  let best = -Infinity, run = 0, prev = null, i = 0;
  while (i < times.length) {
    const t = times[i];
    let count = 0;
    while (i < times.length && times[i] === t) { count++; i++; }
    run = prev === null ? count : count + Math.max(0, run - (t - prev));
    prev = t;
    if (run > best) best = run;
  }
  return best;
}

function maxTestingEfficiency(arrivalTime) { return solve(arrivalTime); }

module.exports = solve;
module.exports.maxTestingEfficiency = maxTestingEfficiency;
