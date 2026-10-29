"use strict";
// Hack2Hire 67801e4c6fee41e51af73dda (Student Reading Textbook) over an INFERRED spec; qualification unknown.

function ceilDiv(a, b) {
  let q = Math.floor(a / b);
  while (q * b > a) q--;
  while ((q + 1) * b <= a) q++;
  return q * b < a ? q + 1 : q;
}

function solve(pages, days) {
  if (days < pages.length) return -1;
  let total = 0, hi = 0;
  for (const p of pages) { total += p; if (p > hi) hi = p; }
  let lo = Math.max(1, ceilDiv(total, days));
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    let used = 0;
    for (let i = 0; i < pages.length && used <= days; i++) used += ceilDiv(pages[i], mid);
    if (used <= days) hi = mid; else lo = mid + 1;
  }
  return lo;
}

function minimumPagesPerDay(pages, days) { return solve(pages, days); }

module.exports = solve;
module.exports.minimumPagesPerDay = minimumPagesPerDay;
