"use strict";
// Hack2Hire 67873a44e20f8f324213c29a (Make Power Non-decreasing) over an INFERRED spec; qualification unknown.

function solve(power) {
  let total = 0;
  for (let i = 1; i < power.length; i++) {
    if (power[i - 1] > power[i]) total += power[i - 1] - power[i];
  }
  return total;
}

function minimalIncreaseSum(power) { return solve(power); }

module.exports = solve;
module.exports.minimalIncreaseSum = minimalIncreaseSum;
