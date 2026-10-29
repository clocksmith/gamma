"use strict";
// Hack2Hire 69a4da066e73e4abccc9c43f (Minimum Batteries for Call Duration) over an INFERRED spec; qualification unknown.

function lowerBound(arr, target) {
  let lo = 0, hi = arr.length;
  while (lo < hi) {
    const mid = (lo + hi) >>> 1;
    if (arr[mid] < target) lo = mid + 1; else hi = mid;
  }
  return lo;
}

function solve(usageDuration, chargeTime, duration) {
  const n = usageDuration.length;
  const prefix = new Array(n + 1);
  prefix[0] = 0;
  for (let i = 0; i < n; i++) prefix[i + 1] = prefix[i] + usageDuration[i];
  const total = prefix[n];
  if (duration <= total) return lowerBound(prefix, duration);
  for (let i = 0; i < n; i++) {
    if (chargeTime[i] > total - usageDuration[i]) {
      if (duration <= total + prefix[i]) return n + lowerBound(prefix, duration - total);
      return -1;
    }
  }
  const rest = duration - total;
  const full = (rest - 1 - (rest - 1) % total) / total;
  return n + full * n + lowerBound(prefix, rest - full * total);
}

function minBatteries(usageDuration, chargeTime, duration) { return solve(usageDuration, chargeTime, duration); }

module.exports = solve;
module.exports.minBatteries = minBatteries;
