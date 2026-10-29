"use strict";
// Hack2Hire 681aa38c0a6e86cbf10c58f9 (Shortest Hiking Distance) over an INFERRED spec; qualification unknown.

function days(t, limit, cap) {
  let count = 1, start = 0;
  for (let i = 1; i < t.length; i++) {
    if (t[i] - start > limit) {
      if (++count > cap) return count;
      start = t[i - 1];
    }
  }
  return count;
}

function solve(t, k) {
  const n = t.length;
  if (n === 1) return 0;
  let lo = 0, hi = t[n - 1];
  for (let i = 0; i + 1 < n; i++) if (t[i + 1] - t[i] > lo) lo = t[i + 1] - t[i];
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    if (days(t, mid, k + 1) <= k + 1) hi = mid; else lo = mid + 1;
  }
  return lo;
}

function minMaxDailyDistance(t, k) { return solve(t, k); }

module.exports = solve;
module.exports.minMaxDailyDistance = minMaxDailyDistance;
