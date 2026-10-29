"use strict";
// Hack2Hire 68f82cd8d7ff180d0ab950c7 (Count of Stable Subarrays) over an INFERRED spec; qualification unknown.

function solve(capacity) {
  const n = capacity.length;
  const prefix = new Array(n + 1).fill(0);
  for (let i = 0; i < n; i++) prefix[i + 1] = prefix[i] + capacity[i];
  const seen = new Map();
  let total = 0;
  for (let r = 2; r < n; r++) {
    const left = capacity[r - 2] + "," + prefix[r - 1];
    seen.set(left, (seen.get(left) || 0) + 1);
    total += seen.get(capacity[r] + "," + (prefix[r] - capacity[r])) || 0;
  }
  return total;
}

function countStableSegments(capacity) { return solve(capacity); }

module.exports = solve;
module.exports.countStableSegments = countStableSegments;
