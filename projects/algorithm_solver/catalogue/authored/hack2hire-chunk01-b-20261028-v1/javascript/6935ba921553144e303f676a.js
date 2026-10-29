"use strict";
// Hack2Hire 6935ba921553144e303f676a (Find Cluster Mode and Median, variant 1: mode). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.
// Deterministic model of the distributed protocol: local counts, hash shuffle by value mod k, per-reducer best, coordinator merge.

function solve(slices) {
  const k = slices.length, reducers = [];
  for (let i = 0; i < k; i++) reducers.push(new Map());
  for (const part of slices) {
    const local = new Map();
    for (const value of part) local.set(value, (local.get(value) || 0) + 1);
    for (const [value, count] of local) {
      const bucket = reducers[((value % k) + k) % k];
      bucket.set(value, (bucket.get(value) || 0) + count);
    }
  }
  let bestValue = null, bestCount = 0;
  for (const bucket of reducers) {
    for (const [value, count] of bucket) {
      if (count > bestCount || (count === bestCount && value < bestValue)) {
        bestValue = value;
        bestCount = count;
      }
    }
  }
  return bestValue;
}

function findClusterMode(slices) { return solve(slices); }
module.exports = solve;
module.exports.findClusterMode = findClusterMode;
