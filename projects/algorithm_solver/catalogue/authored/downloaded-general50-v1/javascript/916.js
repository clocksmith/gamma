'use strict';

// 916. Word Subsets (Medium).
// Specification: https://leetcode.com/problems/word-subsets/description/
function counts(word) {
  const c = {};
  for (const ch of word) c[ch] = (c[ch] || 0) + 1;
  return c;
}
function solve(words1, words2) {
  const need = {};
  for (const word of words2) {
    const c = counts(word);
    for (const ch in c) need[ch] = Math.max(need[ch] || 0, c[ch]);
  }
  const result = [];
  for (const word of words1) {
    const c = counts(word);
    let ok = true;
    for (const ch in need) { if ((c[ch] || 0) < need[ch]) { ok = false; break; } }
    if (ok) result.push(word);
  }
  return result;
}
const wordSubsets = solve;
class Solution { wordSubsets(words1, words2) { return solve(words1, words2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, wordSubsets };
