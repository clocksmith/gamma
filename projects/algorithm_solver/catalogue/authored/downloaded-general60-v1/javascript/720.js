'use strict';

// 720. Longest Word in Dictionary (Easy).
// Specification: https://leetcode.com/problems/longest-word-in-dictionary/description/
function solve(words) {
  const ordered = words.slice().sort((a, b) => b.length - a.length || a.localeCompare(b));
  const built = new Set(['']);
  for (const word of words) built.add(word);
  for (const word of ordered) {
    let ok = true;
    for (let i = 1; i < word.length; i++) { if (!built.has(word.slice(0, i))) { ok = false; break; } }
    if (ok) return word;
  }
  return '';
}
const longestWord = solve;
class Solution { longestWord(words) { return solve(words); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestWord };
