"use strict";
// Hack2Hire 68fd382047bea664c0bba31e (Non-Consecutive Process Scheduling) over an INFERRED spec; qualification unknown.

const MOD = 1000000007n;

function solve(nProcesses, nIntervals) {
  let result = BigInt(nProcesses) % MOD, base = BigInt(nProcesses - 1) % MOD, exponent = nIntervals - 1;
  while (exponent > 0) {
    if (exponent % 2 === 1) result = result * base % MOD;
    base = base * base % MOD;
    exponent = Math.floor(exponent / 2);
  }
  return Number(result);
}

function countSchedules(nProcesses, nIntervals) { return solve(nProcesses, nIntervals); }

module.exports = solve;
module.exports.countSchedules = countSchedules;
