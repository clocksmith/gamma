"use strict";
// Hack2Hire 6a74eeddd713d873ca7a8195 (Minimum Device Procurement Cost) over an INFERRED spec; qualification unknown.

function solve(x, y, edgeCost, inputCost, bundleCost) {
  let best = Infinity;
  for (const b of [0, Math.min(x, y), Math.max(x, y)]) {
    const cost = b * bundleCost + (x > b ? x - b : 0) * edgeCost + (y > b ? y - b : 0) * inputCost;
    if (cost < best) best = cost;
  }
  return best;
}

function minimumCost(x, y, edgeCost, inputCost, bundleCost) { return solve(x, y, edgeCost, inputCost, bundleCost); }

module.exports = solve;
module.exports.minimumCost = minimumCost;
