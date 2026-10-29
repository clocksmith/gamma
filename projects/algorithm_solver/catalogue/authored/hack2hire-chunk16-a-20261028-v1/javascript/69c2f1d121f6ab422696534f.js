"use strict";
// Hack2Hire 69c2f1d121f6ab422696534f (Grep With Context Lines, variant 1 of 2) over an INFERRED spec; qualification unknown.

function solve(lines, target, linesAround) {
  const n = lines.length;
  const out = [];
  let nextIndex = 0;
  for (let j = 0; j < n; j++) {
    if (!lines[j].includes(target)) continue;
    const start = Math.max(nextIndex, j - linesAround);
    const stop = Math.min(n, j + linesAround + 1);
    for (let i = start; i < stop; i++) out.push(lines[i]);
    if (stop > nextIndex) nextIndex = stop;
  }
  return out;
}

function grepWithContext(lines, target, linesAround) { return solve(lines, target, linesAround); }

module.exports = solve;
module.exports.grepWithContext = grepWithContext;
