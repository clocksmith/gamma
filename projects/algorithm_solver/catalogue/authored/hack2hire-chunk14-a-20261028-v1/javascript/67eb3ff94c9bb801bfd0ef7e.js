"use strict";
// Hack2Hire 67eb3ff94c9bb801bfd0ef7e (Stock Trades Matching, variant 2 of 2) over an INFERRED spec; qualification unknown.

function cmp(a, b) { return a < b ? -1 : a > b ? 1 : 0; }

function solve(house, street) {
  const counts = new Map();
  for (const trade of street) counts.set(trade, (counts.get(trade) || 0) + 1);
  const groups = new Map();
  const group = (key) => {
    let g = groups.get(key);
    if (!g) { g = [[], []]; groups.set(key, g); }
    return g;
  };
  for (const trade of house) {
    const c = counts.get(trade) || 0;
    if (c > 0) counts.set(trade, c - 1);
    else group(trade.slice(0, 11))[0].push(trade);
  }
  for (const [trade, count] of counts) for (let i = 0; i < count; i++) group(trade.slice(0, 11))[1].push(trade);
  const left = [];
  for (const [sideHouse, sideStreet] of groups.values()) {
    sideHouse.sort(cmp);
    sideStreet.sort(cmp);
    const paired = Math.min(sideHouse.length, sideStreet.length);
    for (let i = paired; i < sideHouse.length; i++) left.push(sideHouse[i]);
    for (let i = paired; i < sideStreet.length; i++) left.push(sideStreet[i]);
  }
  left.sort(cmp);
  return left;
}

function unmatchedTradesWithAttributes(house, street) { return solve(house, street); }

module.exports = solve;
module.exports.unmatchedTradesWithAttributes = unmatchedTradesWithAttributes;
