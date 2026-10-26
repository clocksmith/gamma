'use strict';

// 734. Sentence Similarity (Easy).
// Specification: https://leetcode.com/problems/sentence-similarity/description/
// O(n + p) expected word operations, O(p) space; similarity is symmetric, not transitive.
function solve(sentence1, sentence2, similarPairs) {
  if (sentence1.length !== sentence2.length) return false;
  const neighbors = new Map();
  for (const [first, second] of similarPairs) {
    if (!neighbors.has(first)) neighbors.set(first, new Set());
    if (!neighbors.has(second)) neighbors.set(second, new Set());
    neighbors.get(first).add(second);
    neighbors.get(second).add(first);
  }
  for (let index = 0; index < sentence1.length; index++) {
    const first = sentence1[index];
    const second = sentence2[index];
    if (first !== second && !(neighbors.has(first) && neighbors.get(first).has(second))) return false;
  }
  return true;
}

const areSentencesSimilar = solve;
class Solution {
  areSentencesSimilar(sentence1, sentence2, similarPairs) { return solve(sentence1, sentence2, similarPairs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, areSentencesSimilar };
