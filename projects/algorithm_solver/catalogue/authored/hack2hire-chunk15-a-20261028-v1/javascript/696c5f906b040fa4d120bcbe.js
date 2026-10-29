"use strict";
// Hack2Hire 696c5f906b040fa4d120bcbe (Datapoint Window Sum by Tag, variant 2 of 2) over an INFERRED spec; qualification unknown.

function solve(datapoints, tag, k) {
  const values = [];
  for (const point of datapoints) if (point.tags.includes(tag)) values.push(point.value);
  const result = [];
  let total = 0;
  for (let i = 0; i < values.length; i++) {
    total += values[i];
    if (i >= k) total -= values[i - k];
    result.push(total);
  }
  return result;
}

function lastKSums(datapoints, tag, k) { return solve(datapoints, tag, k); }

module.exports = solve;
module.exports.lastKSums = lastKSums;
