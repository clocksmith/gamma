"use strict";
// Hack2Hire 6a31cd3f5117d1b543567dbe (Minimum Redistribution Cost) over an INFERRED spec; qualification unknown.

function solve(products) {
  const n = products.length;
  let sum = 0;
  for (const v of products) sum += v;
  const average = sum / n;
  let prefix = 0, total = 0, low = Infinity, high = -Infinity;
  for (const v of products) {
    prefix += v - average;
    total += prefix;
    if (prefix < low) low = prefix;
    if (prefix > high) high = prefix;
  }
  const clockwise = total - n * low;
  const counterclockwise = n * high - total;
  return clockwise < counterclockwise ? clockwise : counterclockwise;
}

function minRedistributionCost(products) { return solve(products); }

module.exports = solve;
module.exports.minRedistributionCost = minRedistributionCost;
