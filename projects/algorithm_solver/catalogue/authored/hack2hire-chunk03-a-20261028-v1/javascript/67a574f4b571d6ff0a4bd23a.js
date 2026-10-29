"use strict";
// Hack2Hire 67a574f4b571d6ff0a4bd23a (Maximum Stability) over an INFERRED spec; qualification unknown.

function solve(availability, reliability) {
  const order = availability.map((_, i) => i).sort((a, b) => availability[b] - availability[a]);
  let best = 0, running = 0;
  for (const i of order) {
    running += reliability[i];
    if (availability[i] * running > best) best = availability[i] * running;
  }
  return best;
}

function maxStability(availability, reliability) { return solve(availability, reliability); }

module.exports = solve;
module.exports.maxStability = maxStability;
