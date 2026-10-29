"use strict";
// Hack2Hire 6a513eaa665efda9311f609d (Optimal Stock Price Subsequence) over an INFERRED spec; qualification unknown.

function solve(stockPrice) {
  const n = stockPrice.length;
  const keys = [...new Set(stockPrice.map((p, i) => p + i))].sort((a, b) => a - b);
  const rank = new Map();
  keys.forEach((k, i) => rank.set(k, i + 1));
  const m = keys.length;
  const tree = new Array(m + 1).fill(0); // prefix maximum of non-negative dp values by key
  let best = null;
  for (let i = 0; i < n; i++) {
    const k = rank.get(stockPrice[i] + i);
    let base = 0;
    for (let j = k; j > 0; j -= j & -j) if (tree[j] > base) base = tree[j];
    const value = stockPrice[i] + base;
    if (best === null || value > best) best = value;
    for (let j = k; j <= m; j += j & -j) if (tree[j] < value) tree[j] = value;
  }
  return best;
}

function maxBalancedSum(stockPrice) { return solve(stockPrice); }

module.exports = solve;
module.exports.maxBalancedSum = maxBalancedSum;
