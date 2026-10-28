'use strict';

// 692. Top K Frequent Words (Medium).
// Specification: https://leetcode.com/problems/top-k-frequent-words/description/
function solve(words, k) {
  const counts = new Map();
  for (const word of words) counts.set(word, (counts.get(word) || 0) + 1);
  const entries = [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  return entries.slice(0, k).map(([word]) => word);
}
const topKFrequent = solve;
class Solution { topKFrequent(words, k) { return solve(words, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, topKFrequent };
