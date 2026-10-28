'use strict';

// 1647. Minimum Deletions to Make Character Frequencies Unique (Medium).
// Specification: https://leetcode.com/problems/minimum-deletions-to-make-character-frequencies-unique/description/
function solve(s) {
  const counts = {};
  for (const ch of s) counts[ch] = (counts[ch] || 0) + 1;
  const frequencies = Object.values(counts).sort((a, b) => b - a);
  const used = new Set();
  let deletions = 0;
  for (let freq of frequencies) {
    while (freq > 0 && used.has(freq)) { freq--; deletions++; }
    if (freq > 0) used.add(freq);
  }
  return deletions;
}
const minDeletions = solve;
class Solution { minDeletions(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minDeletions };
