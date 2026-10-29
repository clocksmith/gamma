"use strict";
// Hack2Hire 6a987edf0ca9cc4e1c78a9a5 (Final Values by Source Priority) over an INFERRED spec; qualification unknown.

function solve(sources) {
  const final = new Map();
  for (const row of sources) {
    for (const entry of row) {
      const cut = entry.indexOf(":");
      final.set(entry.slice(0, cut), entry.slice(cut + 1));
    }
  }
  const keys = [...final.keys()].sort();
  return keys.map((k) => k + ":" + final.get(k));
}

function finalValues(sources) { return solve(sources); }

module.exports = solve;
module.exports.finalValues = finalValues;
