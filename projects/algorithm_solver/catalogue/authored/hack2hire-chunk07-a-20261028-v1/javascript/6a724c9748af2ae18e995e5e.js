"use strict";
// Hack2Hire 6a724c9748af2ae18e995e5e (Maximum Distinct Split Sum) over an INFERRED spec; qualification unknown.

function solve(arr) {
  const n = arr.length, suffix = new Int32Array(n + 1);
  let seen = new Set();
  for (let i = n - 1; i >= 0; i--) { seen.add(arr[i]); suffix[i] = seen.size; }
  seen = new Set();
  let best = 0;
  for (let i = 0; i < n - 1; i++) {
    seen.add(arr[i]);
    if (seen.size + suffix[i + 1] > best) best = seen.size + suffix[i + 1];
  }
  return best;
}

function maxDistinctSplitSum(arr) { return solve(arr); }

module.exports = solve;
module.exports.maxDistinctSplitSum = maxDistinctSplitSum;
