"use strict";
// Original Hack2Hire 68ac50961bf7d2097f647ef5 variant over an INFERRED specification; qualification unknown.
function solve(words) {
  const ordered = [...words].sort(), prefixes = new Set();
  for (let i = 0; i + 1 < ordered.length; i++) if (ordered[i + 1].startsWith(ordered[i])) prefixes.add(ordered[i]);
  return words.filter((word) => !prefixes.has(word));
}
function removePrefixStrings(words) { return solve(words); }
module.exports = solve;
module.exports.removePrefixStrings = removePrefixStrings;
