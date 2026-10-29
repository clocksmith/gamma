"use strict";
// Hack2Hire 67d842e41989183df53824ed (Build the Longest Spike) over an INFERRED spec; qualification unknown.

function solve(arr) {
  if (arr.length === 0) return 0;
  const count = new Map();
  for (const v of arr) count.set(v, (count.get(v) || 0) + 1);
  let peak = -Infinity;
  for (const v of count.keys()) if (v > peak) peak = v;
  let total = 1;
  for (const [v, c] of count) if (v !== peak) total += c >= 2 ? 2 : 1;
  return total;
}

function longestSpike(arr) { return solve(arr); }

module.exports = solve;
module.exports.longestSpike = longestSpike;
