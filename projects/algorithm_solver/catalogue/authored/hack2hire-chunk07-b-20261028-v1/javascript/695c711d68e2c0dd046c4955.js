"use strict";
// Hack2Hire 695c711d68e2c0dd046c4955 (Most Frequent Substring) over an INFERRED spec; qualification unknown.

function solve(str, n) {
  if (n > str.length) return "";
  const counts = new Map();
  for (let i = 0; i + n <= str.length; i++) {
    const w = str.substring(i, i + n);
    counts.set(w, (counts.get(w) || 0) + 1);
  }
  let best = "", bestCount = 0;
  for (const [w, c] of counts) {
    if (c > bestCount || (c === bestCount && w < best)) { best = w; bestCount = c; }
  }
  return best;
}

function mostFrequentSubstring(str, n) { return solve(str, n); }

module.exports = solve;
module.exports.mostFrequentSubstring = mostFrequentSubstring;
