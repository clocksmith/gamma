'use strict';

// 748. Shortest Completing Word (Easy).
// Specification: https://leetcode.com/problems/shortest-completing-word/description/
function countsOf(text) {
  const counts = {};
  for (const ch of text.toLowerCase()) { if (ch >= 'a' && ch <= 'z') counts[ch] = (counts[ch] || 0) + 1; }
  return counts;
}
function solve(licensePlate, words) {
  const need = countsOf(licensePlate);
  let best = null;
  for (const word of words) {
    const have = countsOf(word);
    let ok = true;
    for (const ch in need) { if ((have[ch] || 0) < need[ch]) { ok = false; break; } }
    if (ok && (best === null || word.length < best.length)) best = word;
  }
  return best;
}
const shortestCompletingWord = solve;
class Solution { shortestCompletingWord(licensePlate, words) { return solve(licensePlate, words); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, shortestCompletingWord };
