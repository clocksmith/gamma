"use strict";
// Hack2Hire 69beec3021f6ab4226963c1d (Counting Words in a Text) over an INFERRED spec; qualification unknown.

function solve(text, k) {
  const freq = new Map();
  for (const word of text.toLowerCase().split(' ')) if (word) freq.set(word, (freq.get(word) || 0) + 1);
  if (freq.size === 0) return [];
  const levels = [...new Set(freq.values())].sort((x, y) => y - x);
  const cutoff = levels[Math.min(k, levels.length) - 1];
  const keep = [];
  for (const [word, f] of freq) if (f >= cutoff) keep.push([word, f]);
  keep.sort((x, y) => (y[1] - x[1]) || (x[0] < y[0] ? -1 : x[0] > y[0] ? 1 : 0));
  return keep;
}

function topFrequencyWords(text, k) { return solve(text, k); }

module.exports = solve;
module.exports.topFrequencyWords = topFrequencyWords;
