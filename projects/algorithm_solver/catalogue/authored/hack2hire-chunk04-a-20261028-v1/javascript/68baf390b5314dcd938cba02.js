"use strict";
// Hack2Hire 68baf390b5314dcd938cba02 (Split Stay Booking) over an INFERRED spec; qualification unknown.

function solve(availability, start, end) {
  const prefixEnd = [], suffixStart = [];
  for (const days of availability) {
    const present = new Set(days);
    let a = start - 1;
    while (a < end && present.has(a + 1)) a++;
    let b = end + 1;
    while (b > start && present.has(b - 1)) b--;
    prefixEnd.push(a);
    suffixStart.push(b);
  }
  const n = availability.length, result = [];
  for (let i = 0; i < n; i++) if (prefixEnd[i] === end) result.push([i]);
  for (let i = 0; i < n; i++) {
    const high = Math.min(prefixEnd[i], end - 1);
    for (let j = 0; j < n; j++) if (i !== j && Math.max(start, suffixStart[j] - 1) <= high) result.push([i, j]);
  }
  return result;
}

function findSplitStays(availability, start, end) { return solve(availability, start, end); }

module.exports = solve;
module.exports.findSplitStays = findSplitStays;
