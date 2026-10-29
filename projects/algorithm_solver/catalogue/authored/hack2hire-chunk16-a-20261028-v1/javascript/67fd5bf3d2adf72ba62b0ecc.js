"use strict";
// Hack2Hire 67fd5bf3d2adf72ba62b0ecc (Jaccard Business Similarity) over an INFERRED spec; qualification unknown.

function solve(s1, s2) {
  const a = new Set(s1 ? s1.split(' ') : []);
  const b = new Set(s2 ? s2.split(' ') : []);
  if (a.size === 0 && b.size === 0) return 1.0;
  let common = 0;
  for (const word of a) if (b.has(word)) common++;
  const union = a.size + b.size - common;
  const hundredths = Math.floor((200 * common + union) / (2 * union));
  return hundredths / 100;
}

function jaccardSimilarity(s1, s2) { return solve(s1, s2); }

module.exports = solve;
module.exports.jaccardSimilarity = jaccardSimilarity;
