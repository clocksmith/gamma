"use strict";
// Hack2Hire 68c32db81f64f4312b0a3e26 (F1 Last Lap Improvement, variant 1 of 2) over an INFERRED spec; qualification unknown.

function solve(drivers, lapTimes) {
  let bestKey = null, bestName = null;
  for (let i = 0; i < drivers.length; i++) {
    const laps = lapTimes[i], last = laps[laps.length - 1];
    let sum = 0;
    for (const t of laps) sum += t;
    const key = sum - last - last * (laps.length - 1); // (L - 1) * improvement
    if (bestKey === null || key > bestKey || (key === bestKey && drivers[i] < bestName)) { bestKey = key; bestName = drivers[i]; }
  }
  return bestName;
}

function bestLastLapImprovement(drivers, lapTimes) { return solve(drivers, lapTimes); }

module.exports = solve;
module.exports.bestLastLapImprovement = bestLastLapImprovement;
