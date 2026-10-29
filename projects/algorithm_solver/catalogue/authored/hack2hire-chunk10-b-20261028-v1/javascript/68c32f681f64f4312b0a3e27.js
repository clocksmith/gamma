"use strict";
// Hack2Hire 68c32f681f64f4312b0a3e27 (F1 Last Lap Improvement, variant 2 of 2) over an INFERRED spec; qualification unknown.

function solve(drivers, lapTimes) {
  const keyed = drivers.map((name, i) => {
    const laps = lapTimes[i], last = laps[laps.length - 1];
    let sum = 0;
    for (const t of laps) sum += t;
    return [sum - last - last * (laps.length - 1), name];
  });
  keyed.sort((a, b) => b[0] - a[0] || (a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0));
  return keyed.map((x) => x[1]);
}

function rankLastLapImprovement(drivers, lapTimes) { return solve(drivers, lapTimes); }

module.exports = solve;
module.exports.rankLastLapImprovement = rankLastLapImprovement;
