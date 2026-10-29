"use strict";
// Hack2Hire 6796f907b10bc587828f27b2 (Calculate Total Waiting Time) over an INFERRED spec; qualification unknown.

function bisectRight(a, x) {
  let lo = 0, hi = a.length;
  while (lo < hi) { const mid = (lo + hi) >>> 1; if (a[mid] <= x) lo = mid + 1; else hi = mid; }
  return lo;
}

function solve(arr) {
  const n = arr.length;
  if (n === 0) return 0;
  const ordered = arr.slice().sort((x, y) => x - y);
  const prefix = [0];
  for (const v of ordered) prefix.push(prefix[prefix.length - 1] + v);
  const top = ordered[n - 1];
  const tree = new Array(top + 1).fill(0); // Fenwick tree over values 1..top
  let total = 0;
  for (let i = 0; i < n; i++) {
    const v = arr[i];
    for (let j = v; j <= top; j += j & -j) tree[j]++;
    let smaller = 0;
    for (let j = v - 1; j > 0; j -= j & -j) smaller += tree[j];
    const cut = bisectRight(ordered, v - 1);
    const beforeLastRound = prefix[cut] + (n - cut) * (v - 1);
    const completion = beforeLastRound + (i + 1 - smaller);
    total += completion - v;
  }
  return total;
}

function totalWaitingTime(arr) { return solve(arr); }

module.exports = solve;
module.exports.totalWaitingTime = totalWaitingTime;
