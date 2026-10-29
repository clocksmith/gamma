"use strict";
// Hack2Hire 67d88d261989183df5382503 (Minimum Starting Battery Level) over an INFERRED spec; qualification unknown.

function solve(usage) {
  let prefix = 0, peak = 0;
  for (const u of usage) {
    prefix += u;
    if (prefix > peak) peak = prefix;
  }
  return peak + 1;
}

function minStartingBattery(usage) { return solve(usage); }

module.exports = solve;
module.exports.minStartingBattery = minStartingBattery;
