"use strict";
// Hack2Hire 67fdb0ced2adf72ba62b0eda (Vowels Substring) over an INFERRED spec; qualification unknown.

function solve(s) {
  const slot = {a: 0, e: 1, i: 2, o: 3, u: 4};
  let last = [-1, -1, -1, -1, -1], start = 0, total = 0;
  for (let i = 0; i < s.length; i++) {
    const k = slot[s[i]];
    if (k === undefined) { start = i + 1; last = [-1, -1, -1, -1, -1]; continue; }
    last[k] = i;
    const earliest = Math.min(last[0], last[1], last[2], last[3], last[4]);
    if (earliest >= start) total += earliest - start + 1;
  }
  return total;
}

function countVowelSubstrings(s) { return solve(s); }

module.exports = solve;
module.exports.countVowelSubstrings = countVowelSubstrings;
