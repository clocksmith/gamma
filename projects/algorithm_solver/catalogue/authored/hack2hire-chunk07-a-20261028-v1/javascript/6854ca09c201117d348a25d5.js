"use strict";
// Hack2Hire 6854ca09c201117d348a25d5 (Longest Semi-Alternating Substring) over an INFERRED spec; qualification unknown.

function solve(s) {
  let best = 0, start = 0;
  for (let i = 0; i < s.length; i++) {
    if (i >= 2 && s[i] === s[i - 1] && s[i] === s[i - 2]) start = i - 1;
    if (i - start + 1 > best) best = i - start + 1;
  }
  return best;
}

function longestSemiAlternating(s) { return solve(s); }

module.exports = solve;
module.exports.longestSemiAlternating = longestSemiAlternating;
