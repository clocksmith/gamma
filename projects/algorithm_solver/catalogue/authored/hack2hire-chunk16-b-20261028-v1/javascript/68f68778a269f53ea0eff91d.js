"use strict";
// Hack2Hire 68f68778a269f53ea0eff91d (Product Price Query System) over an INFERRED spec; qualification unknown.

// Dates become integers yyyymmdd; each item's (date, local index) pairs are packed into one number below 2**53 and sorted numerically.
function dateKey(date) {
  return Number(date.slice(0, 4)) * 10000 + Number(date.slice(5, 7)) * 100 + Number(date.slice(8, 10));
}

function solve(log, queries) {
  const items = new Map();
  for (const entry of log) {
    const second = entry.lastIndexOf(", ");
    const first = entry.lastIndexOf(", ", second - 1);
    const item = entry.slice(0, first);
    let rows = items.get(item);
    if (rows === undefined) { rows = {dates: [], prices: []}; items.set(item, rows); }
    rows.dates.push(dateKey(entry.slice(first + 2, second)));
    rows.prices.push(Number(entry.slice(second + 2)));
  }
  const index = new Map();
  for (const [item, rows] of items) {
    const packed = new Float64Array(rows.dates.length);
    for (let i = 0; i < packed.length; i++) packed[i] = rows.dates[i] * 131072 + i;
    packed.sort();
    const dates = new Float64Array(packed.length), prices = new Float64Array(packed.length);
    for (let i = 0; i < packed.length; i++) {
      const local = packed[i] % 131072;
      dates[i] = rows.dates[local];
      prices[i] = rows.prices[local];
    }
    index.set(item, {dates, prices});
  }
  const out = [];
  for (const [item, date] of queries) {
    const found = index.get(item);
    if (found === undefined) { out.push(-1); continue; }
    const key = dateKey(date);
    let lo = 0, hi = found.dates.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (found.dates[mid] <= key) lo = mid + 1; else hi = mid;
    }
    out.push(lo ? found.prices[lo - 1] : -1);
  }
  return out;
}

function getPrices(log, queries) { return solve(log, queries); }

module.exports = solve;
module.exports.getPrices = getPrices;
