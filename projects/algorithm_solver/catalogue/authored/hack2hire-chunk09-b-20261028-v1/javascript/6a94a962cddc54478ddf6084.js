"use strict";
// Hack2Hire 6a94a962cddc54478ddf6084 (Calculate Process Starvation) over an INFERRED spec; qualification unknown.

function solve(priorities) {
  const n = priorities.length, suffixMin = new Array(n);
  let low = Infinity;
  for (let j = n - 1; j >= 0; j--) {
    if (priorities[j] < low) low = priorities[j];
    suffixMin[j] = low;
  }
  const out = new Array(n).fill(0);
  for (let i = 0; i < n; i++) {
    let lo = 0, hi = n;  // first index with suffixMin >= priorities[i]
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (suffixMin[mid] < priorities[i]) lo = mid + 1; else hi = mid;
    }
    const j = lo - 1;
    if (j > i) out[i] = j - i;
  }
  return out;
}

function starvationTimes(priorities) { return solve(priorities); }

module.exports = solve;
module.exports.starvationTimes = starvationTimes;
