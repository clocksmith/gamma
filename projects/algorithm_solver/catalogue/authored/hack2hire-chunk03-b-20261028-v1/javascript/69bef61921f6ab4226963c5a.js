"use strict";
// Hack2Hire 69bef61921f6ab4226963c5a (Maximum Throughput) over an INFERRED spec; qualification unknown.

// Exact floor division for non-negative integers below 2**53.
function floorDiv(a, b) {
  let q = Math.floor(a / b);
  while (q * b > a) q--;
  while ((q + 1) * b <= a) q++;
  return q;
}

function solve(throughput, scalingCost, budget) {
  const n = throughput.length;
  const feasible = (target) => {
    let spent = 0;
    for (let i = 0; i < n; i++) {
      const t = throughput[i];
      if (t < target) {
        const upgrades = floorDiv(target + t - 1, t) - 1;
        if (upgrades > budget) return false;
        spent += upgrades * scalingCost[i];
        if (spent > budget) return false;
      }
    }
    return true;
  };
  let lo = Infinity, hi = Infinity;
  for (let i = 0; i < n; i++) {
    lo = Math.min(lo, throughput[i]);
    hi = Math.min(hi, throughput[i] * (1 + floorDiv(budget, scalingCost[i])));
  }
  while (lo < hi) {
    const mid = floorDiv(lo + hi + 1, 2);
    if (feasible(mid)) lo = mid; else hi = mid - 1;
  }
  return lo;
}

function maximumThroughput(throughput, scalingCost, budget) { return solve(throughput, scalingCost, budget); }

module.exports = solve;
module.exports.maximumThroughput = maximumThroughput;
