"use strict";
// Hack2Hire 68102bc42590daeb41a329e6 (Equalize Server Latency) over an INFERRED spec; qualification unknown.

function solve(n, latency) {
  const cost = latency.slice(); // private copy: path sums accumulate here
  let total = 0;
  for (let v = Math.floor(n / 2) - 1; v >= 0; v--) {
    const left = cost[2 * v + 1], right = cost[2 * v + 2];
    total += Math.abs(left - right);
    cost[v] += Math.max(left, right);
  }
  return total;
}

function minIncrements(n, latency) { return solve(n, latency); }

module.exports = solve;
module.exports.minIncrements = minIncrements;
