"use strict";
// Hack2Hire 6a97291f0ca9cc4e1c789d82 (Threshold Alerts) over an INFERRED spec; qualification unknown.

function solve(numCalls, precedingMinutes, alertThreshold) {
  const k = precedingMinutes;
  const need = alertThreshold * k;
  let total = 0, alerts = 0;
  for (let i = 0; i < numCalls.length; i++) {
    total += numCalls[i];
    if (i >= k) total -= numCalls[i - k];
    if (i >= k - 1 && total >= need) alerts++;
  }
  return alerts;
}

function countAlerts(numCalls, precedingMinutes, alertThreshold) { return solve(numCalls, precedingMinutes, alertThreshold); }

module.exports = solve;
module.exports.countAlerts = countAlerts;
