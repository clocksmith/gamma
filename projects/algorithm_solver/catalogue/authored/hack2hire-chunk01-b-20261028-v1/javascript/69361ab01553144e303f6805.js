"use strict";
// Hack2Hire 69361ab01553144e303f6805 (Find Cluster Mode and Median, variant 2: median). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.
// Deterministic model: workers sort locally and answer "how many <= x" probes; the coordinator binary-searches the value range.

function upperBound(sorted, x) {
  let low = 0, high = sorted.length;
  while (low < high) {
    const middle = (low + high) >> 1;
    if (sorted[middle] <= x) low = middle + 1;
    else high = middle;
  }
  return low;
}

function solve(slices) {
  const workers = slices.map((part) => part.slice().sort((a, b) => a - b));
  let total = 0;
  for (const w of workers) total += w.length;
  const kth = (k) => {
    let low = -1e9, high = 1e9;
    while (low < high) {
      const middle = Math.floor((low + high) / 2);
      let count = 0;
      for (const w of workers) count += upperBound(w, middle);
      if (count >= k + 1) high = middle;
      else low = middle + 1;
    }
    return low;
  };
  const a = kth(Math.floor((total - 1) / 2)), b = kth(Math.floor(total / 2));
  return (a + b) / 2;
}

function findClusterMedian(slices) { return solve(slices); }
module.exports = solve;
module.exports.findClusterMedian = findClusterMedian;
