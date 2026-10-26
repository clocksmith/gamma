'use strict';

// 2363. Merge Similar Items (Easy).
// Specification: https://leetcode.com/problems/merge-similar-items/description/
// O(n + m + u log u) time, O(u) space; sum weights by value; return fresh pairs sorted by value.
function solve(items1, items2) {
  const weights = new Map();
  for (const items of [items1, items2]) {
    for (const [value, weight] of items) {
      weights.set(value, (weights.get(value) || 0) + weight);
    }
  }
  const values = Array.from(weights.keys()).sort((a, b) => a - b);
  return values.map(value => [value, weights.get(value)]);
}

const mergeSimilarItems = solve;
class Solution {
  mergeSimilarItems(items1, items2) { return solve(items1, items2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mergeSimilarItems };
