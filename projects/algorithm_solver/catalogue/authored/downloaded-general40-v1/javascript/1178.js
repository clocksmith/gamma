'use strict';

// 1178. Number of Valid Words for Each Puzzle (Medium).
// Specification: https://leetcode.com/problems/number-of-valid-words-for-each-puzzle/description/
function solve(words, puzzles) {
  const mask = (w) => {
    let m = 0;
    for (const ch of w) m |= 1 << (ch.charCodeAt(0) - 97);
    return m;
  };
  const freq = new Map();
  for (const w of words) {
    const m = mask(w);
    freq.set(m, (freq.get(m) || 0) + 1);
  }
  const out = [];
  for (const p of puzzles) {
    const pm = mask(p);
    const first = 1 << (p.charCodeAt(0) - 97);
    let count = 0;
    for (let sub = pm; sub > 0; sub = (sub - 1) & pm) {
      if ((sub & first) !== 0) count += freq.get(sub) || 0;
    }
    out.push(count);
  }
  return out;
}
const findNumOfValidWords = solve;
class Solution { findNumOfValidWords(words, puzzles) { return solve(words, puzzles); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findNumOfValidWords };
