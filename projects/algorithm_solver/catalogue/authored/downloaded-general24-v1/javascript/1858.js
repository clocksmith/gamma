'use strict';

// 1858. Longest Word With All Prefixes (Medium).
// Specification: https://leetcode.com/problems/longest-word-with-all-prefixes/description/
function solve(words) {
  const wordSet = new Set(words);
  const candidates = words.slice().sort((a, b) => b.length - a.length || (a < b ? -1 : 1));
  for (const word of candidates) {
    let ok = true;
    for (let length = 1; length < word.length; length++) {
      if (!wordSet.has(word.slice(0, length))) { ok = false; break; }
    }
    if (ok) return word;
  }
  return '';
}
const longestWord = solve;
class Solution { longestWord(words) { return solve(words); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestWord };
