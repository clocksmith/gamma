"use strict";
// Hack2Hire 6913fb43fa8a311e42671e69 (Dependency Version Check, variant 1 of 2) over an INFERRED spec; qualification unknown.

function solve(versions, supported) {
  let lo = 0, hi = versions.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (supported[mid]) hi = mid; else lo = mid + 1;
  }
  return lo < versions.length ? versions[lo] : null;
}

function firstSupported(versions, supported) { return solve(versions, supported); }

module.exports = solve;
module.exports.firstSupported = firstSupported;
