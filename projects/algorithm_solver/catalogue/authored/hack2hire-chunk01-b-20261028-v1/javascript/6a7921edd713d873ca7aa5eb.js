"use strict";
// Hack2Hire 6a7921edd713d873ca7aa5eb (Find Missing Subsequence Words). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

function solve(s, t) {
  const words = s.split(" "), wanted = t === "" ? [] : t.split(" "), missing = [];
  let j = 0;
  for (const word of words) {
    if (j < wanted.length && word === wanted[j]) j++;
    else missing.push(word);
  }
  return missing;
}

function findMissingWords(s, t) { return solve(s, t); }
module.exports = solve;
module.exports.findMissingWords = findMissingWords;
