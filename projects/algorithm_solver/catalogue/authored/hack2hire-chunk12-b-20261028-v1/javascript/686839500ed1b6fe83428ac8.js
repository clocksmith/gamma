"use strict";
// Hack2Hire 686839500ed1b6fe83428ac8 (Minimal Video Score Reduction) over an INFERRED spec; qualification unknown.

function solve(scores, k) {
  const positive = scores.filter((s) => s > 0);
  if (positive.length === 0) return 1;
  if (positive.length > k) return -1;
  let lo = 1, hi = 0;
  for (const s of positive) if (s > hi) hi = s;
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    let ops = 0;
    for (const s of positive) {
      ops += Math.floor((s + mid - 1) / mid);
      if (ops > k) break;
    }
    if (ops <= k) hi = mid; else lo = mid + 1;
  }
  return lo;
}

function minimumDecrement(scores, k) { return solve(scores, k); }

module.exports = solve;
module.exports.minimumDecrement = minimumDecrement;
