"use strict";
// Hack2Hire 67d33f6a488516fd8ad5a064 (Minimal Board Length for Holes) over an INFERRED spec; qualification unknown.

function solve(arr) {
  const a = Float64Array.from(arr).sort(), n = a.length;
  let best = n > 1 ? Infinity : 0;
  for (let i = 0; i + 1 < n; i++) best = Math.min(best, Math.max(a[i] - a[0], a[n - 1] - a[i + 1]));
  return Math.max(1, best);
}

function minimalBoardLength(arr) { return solve(arr); }

module.exports = solve;
module.exports.minimalBoardLength = minimalBoardLength;
