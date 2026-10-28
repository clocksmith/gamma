'use strict';

// 819. Most Common Word (Easy).
// Specification: https://leetcode.com/problems/most-common-word/description/
function solve(paragraph, banned) {
  const bannedSet = new Set(banned);
  const counts = {};
  const words = paragraph.toLowerCase().split(/[^a-z]+/).filter(Boolean);
  let best = ''; let bestCount = 0;
  for (const word of words) {
    if (bannedSet.has(word)) continue;
    counts[word] = (counts[word] || 0) + 1;
    if (counts[word] > bestCount) { bestCount = counts[word]; best = word; }
  }
  return best;
}
const mostCommonWord = solve;
class Solution { mostCommonWord(paragraph, banned) { return solve(paragraph, banned); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, mostCommonWord };
