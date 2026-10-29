"use strict";
// Hack2Hire 677041e0366afdc1233e4ff4 (Find Redundant Substring) over an INFERRED spec; qualification unknown.

function solve(word, a, b) {
  const vowelStep = 1 - a;
  const consonantStep = 1 - b;
  const seen = new Map([[0, 1]]);
  let key = 0;
  let total = 0;
  for (const ch of word) {
    key += "aeiou".includes(ch) ? vowelStep : consonantStep;
    const count = seen.get(key) || 0;
    total += count;
    seen.set(key, count + 1);
  }
  return total;
}

function countRedundantSubstrings(word, a, b) { return solve(word, a, b); }

module.exports = solve;
module.exports.countRedundantSubstrings = countRedundantSubstrings;
