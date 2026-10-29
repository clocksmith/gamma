"use strict";
// Hack2Hire 67d8a1d71989183df538251a (Maximize Server Throughput) over an INFERRED spec; qualification unknown.

function solve(hostThroughput) {
  const values = Float64Array.from(hostThroughput).sort().reverse();
  let total = 0;
  const clusters = Math.floor(values.length / 3);
  for (let i = 0; i < clusters; i++) total += values[2 * i + 1];
  return total;
}

function maximizeThroughput(hostThroughput) { return solve(hostThroughput); }

module.exports = solve;
module.exports.maximizeThroughput = maximizeThroughput;
