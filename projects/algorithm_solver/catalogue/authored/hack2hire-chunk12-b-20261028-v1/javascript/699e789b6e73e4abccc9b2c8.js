"use strict";
// Hack2Hire 699e789b6e73e4abccc9b2c8 (Minimum Idleness After K Flips) over an INFERRED spec; qualification unknown.

function solve(s, k) {
  const n = s.length;
  const runs = [];
  let start = 0, longest = 0, mismatch = 0;
  for (let i = 1; i <= n; i++) {
    if (i === n || s[i] !== s[start]) {
      runs.push(i - start);
      if (i - start > longest) longest = i - start;
      start = i;
    }
  }
  for (let i = 0; i < n; i++) if (s[i] !== (i % 2 === 0 ? "a" : "b")) mismatch++;
  if (Math.min(mismatch, n - mismatch) <= k) return 1;
  let lo = 2, hi = longest;
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    let need = 0;
    for (const r of runs) need += Math.floor(r / (mid + 1));
    if (need <= k) hi = mid; else lo = mid + 1;
  }
  return lo;
}

function minIdleness(s, k) { return solve(s, k); }

module.exports = solve;
module.exports.minIdleness = minIdleness;
