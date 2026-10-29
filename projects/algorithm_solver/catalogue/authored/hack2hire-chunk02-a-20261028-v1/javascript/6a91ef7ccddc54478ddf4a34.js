"use strict";
// Hack2Hire 6a91ef7ccddc54478ddf4a34 (Highest Average Score); INFERRED spec; qualification unknown.
// |sum| <= 10^14 and count <= 10^5, so cross products stay exact as BigInt; floor division is exact integer arithmetic.
function solve(scores) {
  const totals = new Map();
  for (const [name, score] of scores) {
    const e = totals.get(name) || [0, 0];
    e[0] += Number(score); e[1] += 1; totals.set(name, e);
  }
  let best = null;
  for (const [total, count] of totals.values()) {
    if (best === null || BigInt(total) * BigInt(best[1]) > BigInt(best[0]) * BigInt(count)) best = [total, count];
  }
  if (best === null) return 0;
  const [a, b] = best, r = ((a % b) + b) % b;
  return (a - r) / b;
}
function highestAverageScore(scores) { return solve(scores); }
module.exports = solve;
module.exports.highestAverageScore = highestAverageScore;
