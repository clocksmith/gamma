"use strict";
// Hack2Hire 69efd5e296981f58ae1f6dc7 (Max Levels from Each Index) over an INFERRED spec; qualification unknown.

function solve(layers, energy, K) {
  const n = layers.length, prefix = new Array(n + 1).fill(0), out = [];
  for (let i = 0; i < n; i++) prefix[i + 1] = prefix[i] + layers[i];
  let j = 0;
  for (let i = 0; i < n; i++) {
    if (j < i) j = i;
    const limit = K + prefix[i];
    while (j < n && prefix[j + 1] + energy[j] <= limit) j++;
    out.push(j - i);
  }
  return out;
}

function maxLevels(layers, energy, K) { return solve(layers, energy, K); }

module.exports = solve;
module.exports.maxLevels = maxLevels;
