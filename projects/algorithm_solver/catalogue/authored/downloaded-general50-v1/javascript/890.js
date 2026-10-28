'use strict';

// 890. Find and Replace Pattern (Medium).
// Specification: https://leetcode.com/problems/find-and-replace-pattern/description/
function matches(word, pattern) {
  const w2p = new Map(); const p2w = new Map();
  for (let i = 0; i < word.length; i++) {
    const w = word[i]; const p = pattern[i];
    if (w2p.has(w) && w2p.get(w) !== p) return false;
    if (p2w.has(p) && p2w.get(p) !== w) return false;
    w2p.set(w, p); p2w.set(p, w);
  }
  return true;
}
function solve(words, pattern) { return words.filter((w) => matches(w, pattern)); }
const findAndReplacePattern = solve;
class Solution { findAndReplacePattern(words, pattern) { return solve(words, pattern); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findAndReplacePattern };
