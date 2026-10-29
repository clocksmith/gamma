"use strict";
// Hack2Hire 699926ca6e73e4abccc9a376 (Warehouse Package Allocation) over an INFERRED spec; qualification unknown.

function solve(centerCapacity, dailyLog) {
  const n = centerCapacity.length;
  const nxt = new Array(n), prv = new Array(n), got = new Array(n).fill(0);
  for (let i = 0; i < n; i++) { nxt[i] = (i + 1) % n; prv[i] = (i - 1 + n) % n; }
  let cur = 0, used = 0;
  for (const entry of dailyLog) {
    if (entry === "PACKAGE") {
      got[cur]++;
      used++;
      if (used === centerCapacity[cur]) { cur = nxt[cur]; used = 0; }
    } else {
      const i = Number(entry.slice(8)), p = prv[i], q = nxt[i];
      nxt[p] = q;
      prv[q] = p;
      if (i === cur) { cur = q; used = 0; }
    }
  }
  let best = 0;
  for (let i = 1; i < n; i++) if (got[i] >= got[best]) best = i;
  return best;
}

function busiestCenter(centerCapacity, dailyLog) { return solve(centerCapacity, dailyLog); }

module.exports = solve;
module.exports.busiestCenter = busiestCenter;
