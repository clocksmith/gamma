"use strict";

// string_unit = unicode_codepoint: a non-BMP character is one unit, matching
// Python str and the reference. The Array.from copy is charged as O(n) space.
function solve(word) {
  const chars = Array.from(word);
  const n = chars.length;
  const total = 1 << n;
  const out = new Array(total);
  for (let mask = 0; mask < total; mask++) {
    let s = "";
    let cnt = 0;
    for (let i = 0; i < n; i++) {
      if ((mask >> i) & 1) {
        cnt++;
      } else {
        if (cnt > 0) {
          s += String(cnt);
          cnt = 0;
        }
        s += chars[i];
      }
    }
    if (cnt > 0) s += String(cnt);
    out[mask] = s;
  }
  return out;
}

function generateAbbreviations(word) {
  return solve(word);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.generateAbbreviations = generateAbbreviations;
if (typeof Solution !== "undefined") solve.Solution = Solution;
