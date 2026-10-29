"use strict";
// Hack2Hire 6a08e02abd4165b6d480ffa1 (Camera Motion Detection, variant 2) over an INFERRED spec; qualification unknown.
function periods(times, intensities, threshold) {
  const result = [];
  let start = null;
  for (let i = 0; i < intensities.length; i++) {
    if (intensities[i] < threshold) continue;
    if (start === null) start = times[i];
    if (i + 1 === intensities.length || intensities[i + 1] < threshold) { result.push([start, times[i]]); start = null; }
  }
  return result;
}
function solve(timesA, intensitiesA, timesB, intensitiesB, threshold) {
  const first = periods(timesA, intensitiesA, threshold), second = periods(timesB, intensitiesB, threshold), result = [];
  let i = 0, j = 0;
  while (i < first.length && j < second.length) {
    const low = Math.max(first[i][0], second[j][0]), high = Math.min(first[i][1], second[j][1]);
    if (low <= high) result.push([low, high]);
    if (first[i][1] < second[j][1]) i++; else j++;
  }
  return result;
}
function overlappingMotion(timesA, intensitiesA, timesB, intensitiesB, threshold) { return solve(timesA, intensitiesA, timesB, intensitiesB, threshold); }
module.exports = solve;
module.exports.overlappingMotion = overlappingMotion;
