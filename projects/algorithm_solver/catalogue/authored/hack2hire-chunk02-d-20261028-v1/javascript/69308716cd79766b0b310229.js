"use strict";
// Hack2Hire 69308716cd79766b0b310229 (Generate Function Profiling Events, level 3) over an INFERRED spec; qualification unknown.

function parseSamples(samples) {
  return samples.map((sample) => {
    const colon = sample.indexOf(":");
    const stack = sample.slice(colon + 1);
    return [Number(sample.slice(0, colon)), stack ? stack.split("->") : []];
  });
}

function solve(samples) {
  const rows = parseSamples(samples);
  const total = new Map();
  rows.forEach(([time, stack], index) => {
    for (const name of stack) if (!total.has(name)) total.set(name, 0);
    if (stack.length && index + 1 < rows.length) {
      const inner = stack[stack.length - 1];
      total.set(inner, total.get(inner) + rows[index + 1][0] - time);
    }
  });
  return [...total.keys()].sort().map((name) => [name, total.get(name)]);
}

function exclusiveTimes(samples) { return solve(samples); }

module.exports = solve;
module.exports.exclusiveTimes = exclusiveTimes;
