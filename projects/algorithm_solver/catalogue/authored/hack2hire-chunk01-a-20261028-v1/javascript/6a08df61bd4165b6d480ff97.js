"use strict";
// Hack2Hire 6a08df61bd4165b6d480ff97 (Camera Motion Detection, variant 1) over an INFERRED spec; qualification unknown.
function solve(times, intensities, threshold) {
  const result = [];
  let start = null;
  for (let i = 0; i < intensities.length; i++) {
    if (intensities[i] < threshold) continue;
    if (start === null) start = times[i];
    if (i + 1 === intensities.length || intensities[i + 1] < threshold) { result.push([start, times[i]]); start = null; }
  }
  return result;
}
function motionPeriods(times, intensities, threshold) { return solve(times, intensities, threshold); }
module.exports = solve;
module.exports.motionPeriods = motionPeriods;
