"use strict";
// Hack2Hire 69e93b39fbaf3da6418286bb (Purchase Optimization) over an INFERRED spec; qualification unknown.

function solve(prices, pos, amount) {
  const prefix = [0];
  for (const p of prices) prefix.push(prefix[prefix.length - 1] + p);
  return pos.map((p, j) => {
    const target = prefix[p - 1] + amount[j];
    let lo = p - 1, hi = prefix.length;  // first index with prefix > target
    while (lo < hi) { const mid = (lo + hi) >> 1; if (prefix[mid] <= target) lo = mid + 1; else hi = mid; }
    return lo - p;
  });
}

function maxItems(prices, pos, amount) { return solve(prices, pos, amount); }

module.exports = solve;
module.exports.maxItems = maxItems;
