"use strict";
// Hack2Hire 68001116c48db1937ce88f45 (Count Alert Triggers) over an INFERRED spec; qualification unknown.

function solve(errors, threshold, duration, percent) {
  const n = errors.length;
  if (duration > n) return 0;
  let bad = 0;
  for (let h = 0; h < duration; h++) if (errors[h] > threshold) bad++;
  const need = percent * duration;
  let alerts = bad * 100 >= need ? 1 : 0;
  for (let h = duration; h < n; h++) {
    if (errors[h] > threshold) bad++;
    if (errors[h - duration] > threshold) bad--;
    if (bad * 100 >= need) alerts++;
  }
  return alerts;
}

function countAlerts(errors, threshold, duration, percent) { return solve(errors, threshold, duration, percent); }

module.exports = solve;
module.exports.countAlerts = countAlerts;
