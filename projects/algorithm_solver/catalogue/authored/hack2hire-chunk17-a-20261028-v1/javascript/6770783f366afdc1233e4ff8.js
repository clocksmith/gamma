"use strict";
// Hack2Hire 6770783f366afdc1233e4ff8 (Reduce Gifts) over an INFERRED spec; qualification unknown.

function solve(prices, k, threshold) {
  const ordered = Float64Array.from(prices).sort();
  const n = ordered.length;
  let remaining = n;
  let window = 0;
  for (let i = n - k; i < n; i++) window += ordered[i];
  while (remaining >= k && window > threshold) {
    window -= ordered[remaining - 1];
    remaining--;
    if (remaining >= k) window += ordered[remaining - k];
  }
  return n - remaining;
}

function reduceGifts(prices, k, threshold) { return solve(prices, k, threshold); }

module.exports = solve;
module.exports.reduceGifts = reduceGifts;
