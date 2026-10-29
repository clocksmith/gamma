"use strict";
// Hack2Hire 68bad7afb5314dcd938cb9fe (Top 10 Words, variant 1 of 2) over an INFERRED spec; qualification unknown.

function better(word, count, otherWord, otherCount) {
  return count > otherCount || (count === otherCount && word < otherWord);
}

function solve(s) {
  const counts = new Map();
  for (const match of s.match(/[A-Za-z]+/g) || []) {
    const word = match.toLowerCase();
    counts.set(word, (counts.get(word) || 0) + 1);
  }
  const best = [];
  for (const [word, count] of counts) {
    if (best.length === 10 && !better(word, count, best[9][0], best[9][1])) continue;
    let i = best.length;
    while (i > 0 && better(word, count, best[i - 1][0], best[i - 1][1])) i -= 1;
    best.splice(i, 0, [word, count]);
    if (best.length > 10) best.pop();
  }
  return best;
}

function topTenWords(s) { return solve(s); }

module.exports = solve;
module.exports.topTenWords = topTenWords;
