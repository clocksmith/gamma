"use strict";
// Hack2Hire 67eb34914c9bb801bfd0ef7d (Stock Trades Matching, variant 1 of 2) over an INFERRED spec; qualification unknown.

function cmp(a, b) { return a < b ? -1 : a > b ? 1 : 0; }

function solve(house, street) {
  const counts = new Map();
  for (const trade of street) counts.set(trade, (counts.get(trade) || 0) + 1);
  const left = [];
  for (const trade of house) {
    const c = counts.get(trade) || 0;
    if (c > 0) counts.set(trade, c - 1);
    else left.push(trade);
  }
  for (const [trade, count] of counts) for (let i = 0; i < count; i++) left.push(trade);
  left.sort(cmp);
  return left;
}

function unmatchedTrades(house, street) { return solve(house, street); }

module.exports = solve;
module.exports.unmatchedTrades = unmatchedTrades;
