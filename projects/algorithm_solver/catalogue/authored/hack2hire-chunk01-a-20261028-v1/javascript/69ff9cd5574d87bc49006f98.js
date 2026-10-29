"use strict";
// Hack2Hire 69ff9cd5574d87bc49006f98 (Card Packets with Identical Distribution) over an INFERRED spec; qualification unknown.
// Totals stay below 1e10 (<= 1e5 values times p <= 1e5), so Number arithmetic is exact.
function solve(cardTypes) {
  let limit = 2;
  for (const value of cardTypes) if (value > limit) limit = value;
  const count = new Array(limit + 1).fill(0), total = new Array(limit + 1).fill(0);
  for (const value of cardTypes) { count[value] += 1; total[value] += value; }
  for (let v = 1; v <= limit; v++) { count[v] += count[v - 1]; total[v] += total[v - 1]; }
  const composite = new Uint8Array(limit + 1);
  let best = null;
  for (let p = 2; p <= limit; p++) {
    if (composite[p]) continue;
    for (let multiple = p * p; multiple <= limit; multiple += p) composite[multiple] = 1;
    let cost = 0;
    for (let low = 0; low < limit;) {
      const high = Math.min(low + p, limit);
      cost += (count[high] - count[low]) * (low + p) - (total[high] - total[low]);
      low = high;
    }
    if (best === null || cost < best) best = cost;
  }
  return best;
}
function minAdditionalCards(cardTypes) { return solve(cardTypes); }
module.exports = solve;
module.exports.minAdditionalCards = minAdditionalCards;
