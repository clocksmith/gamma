"use strict";
// Hack2Hire 696c25586b040fa4d120bc21 (Latency Bucket Counter) over an INFERRED spec; qualification unknown.

function solve(latencies, bucketWidth, numOfBuckets) {
  const counts = new Array(numOfBuckets).fill(0), last = numOfBuckets - 1;
  for (const latency of latencies) {
    const bucket = Math.floor(latency / bucketWidth);
    counts[bucket < last ? bucket : last]++;
  }
  return counts;
}

function countLatencyBuckets(latencies, bucketWidth, numOfBuckets) { return solve(latencies, bucketWidth, numOfBuckets); }

module.exports = solve;
module.exports.countLatencyBuckets = countLatencyBuckets;
