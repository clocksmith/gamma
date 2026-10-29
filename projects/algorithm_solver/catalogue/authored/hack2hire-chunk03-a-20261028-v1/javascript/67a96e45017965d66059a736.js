"use strict";
// Hack2Hire 67a96e45017965d66059a736 (Max Square from Mixed Tiles) over an INFERRED spec; qualification unknown.

function feasible(side, small, large) {
  const half = Math.floor(side / 2);
  return side * side - 4 * Math.min(large, half * half) <= small;
}

function solve(M, N) {
  let best = 0;
  for (const parity of [0, 1]) {
    let lo = -1, hi = 50001; // side = 2k + parity; k = -1 means no side of this parity fits
    while (hi - lo > 1) {
      const mid = Math.floor((lo + hi) / 2);
      if (feasible(2 * mid + parity, M, N)) lo = mid; else hi = mid;
    }
    if (lo >= 0) best = Math.max(best, 2 * lo + parity);
  }
  return best;
}

function maxSquareSide(M, N) { return solve(M, N); }

module.exports = solve;
module.exports.maxSquareSide = maxSquareSide;
