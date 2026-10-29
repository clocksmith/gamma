"use strict";
// Hack2Hire 696c54fe6b040fa4d120bca7 (Datapoint Window Sum by Tag, variant 1 of 2) over an INFERRED spec; qualification unknown.

function solve(datapoints, tag, k) {
  const times = [], values = [];
  for (const point of datapoints) {
    if (point.tags.includes(tag)) { times.push(point.timestamp); values.push(point.value); }
  }
  const result = [];
  let left = 0, total = 0;
  for (let i = 0; i < times.length; i++) {
    total += values[i];
    while (times[left] < times[i] - k + 1) { total -= values[left]; left++; }
    result.push(total);
  }
  return result;
}

function windowSums(datapoints, tag, k) { return solve(datapoints, tag, k); }

module.exports = solve;
module.exports.windowSums = windowSums;
