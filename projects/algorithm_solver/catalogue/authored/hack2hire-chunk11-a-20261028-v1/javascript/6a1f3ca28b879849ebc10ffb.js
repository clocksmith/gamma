"use strict";
// Hack2Hire 6a1f3ca28b879849ebc10ffb (Find Pattern Matching Words) over an INFERRED spec; qualification unknown.

function solve(wordDict, pattern) {
  const m = pattern.length, out = [];
  for (const word of wordDict) {
    let previous = new Array(m + 1).fill(false);
    previous[0] = true;
    for (const ch of word) {
      const current = new Array(m + 1).fill(false);
      for (let j = 1; j <= m; j++) {
        const p = pattern[j - 1];
        if (p === ".") current[j] = previous[j - 1] || previous[j]; // consume its first character, or extend
        else current[j] = previous[j - 1] && (p === "?" || p === ch);
      }
      previous = current;
    }
    if (previous[m]) out.push(word);
  }
  return out;
}

function findPatternMatchingWords(wordDict, pattern) { return solve(wordDict, pattern); }

module.exports = solve;
module.exports.findPatternMatchingWords = findPatternMatchingWords;
