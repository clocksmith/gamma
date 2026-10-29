"use strict";
// Original Hack2Hire 6a4fb137665efda9311f561b variant over an INFERRED specification; qualification unknown.
function solve(records, percentile) {
  const counts = new Map();
  let total = 0;
  for (const record of records) {
    const comma = record.indexOf(","), price = Number(record.slice(0, comma)), count = Number(record.slice(comma + 1));
    counts.set(price, (counts.get(price) || 0) + count);
    total += count;
  }
  const need = percentile * total;
  let running = 0;
  for (const price of [...counts.keys()].sort((x, y) => x - y)) {
    running += counts.get(price);
    if (running * 100 >= need) return price;
  }
  return -1;
}
function priceAtPercentile(records, percentile) { return solve(records, percentile); }
module.exports = solve;
module.exports.priceAtPercentile = priceAtPercentile;
