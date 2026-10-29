"use strict";
// Hack2Hire 69141530fa8a311e42671e8f (Dependency Version Check, variant 2 of 2) over an INFERRED spec; qualification unknown.

function solve(versions, supported) {
  const keys = versions.map((v) => v.split(".").map(Number));
  const order = versions.map((_, i) => i).sort((a, b) => keys[a][0] - keys[b][0] || keys[a][1] - keys[b][1] || keys[a][2] - keys[b][2]);
  let lo = 0, hi = order.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (supported[order[mid]]) hi = mid; else lo = mid + 1;
  }
  return lo < order.length ? versions[order[lo]] : null;
}

function firstSupportedUnsorted(versions, supported) { return solve(versions, supported); }

module.exports = solve;
module.exports.firstSupportedUnsorted = firstSupportedUnsorted;
