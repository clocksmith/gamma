"use strict";
// Hack2Hire 67fad958ba41b3368f4e586c (N-gram Split, level 1) over an INFERRED spec; qualification unknown.

function solve(text, bigrams) {
  const pairs = new Set(bigrams), words = text.split(' '), tokens = [];
  let i = 0;
  while (i < words.length) {
    if (i + 1 < words.length && pairs.has(words[i] + ' ' + words[i + 1])) { tokens.push(words[i] + ' ' + words[i + 1]); i += 2; }
    else { tokens.push(words[i]); i += 1; }
  }
  return tokens;
}

function splitBigrams(text, bigrams) { return solve(text, bigrams); }

module.exports = solve;
module.exports.splitBigrams = splitBigrams;
