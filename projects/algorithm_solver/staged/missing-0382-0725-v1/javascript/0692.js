'use strict';

// 692. Top K Frequent Words. Sort distinct words by descending count and ascending lexical order.

function solve(words, k) {
  const counts = new Map();
  for (const word of words) counts.set(word, (counts.get(word) || 0) + 1);
  return Array.from(counts.keys()).sort((a, b) => counts.get(b) - counts.get(a) || (a < b ? -1 : a > b ? 1 : 0)).slice(0, k);
}

const topKFrequent = solve;
class Solution {
  topKFrequent(words, k) { return solve(words, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, topKFrequent };
