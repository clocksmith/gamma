'use strict';

// 1813. Sentence Similarity III: cover the shorter sentence with matching prefix and suffix words.
// O(len(sentence1) + len(sentence2)) time and auxiliary space; inputs are read-only.
function solve(sentence1, sentence2) {
  let first = sentence1.split(' ');
  let second = sentence2.split(' ');
  if (first.length > second.length) [first, second] = [second, first];
  let prefix = 0;
  while (prefix < first.length && first[prefix] === second[prefix]) prefix += 1;
  let suffix = 0;
  while (suffix < first.length - prefix &&
         first[first.length - 1 - suffix] === second[second.length - 1 - suffix]) suffix += 1;
  return prefix + suffix === first.length;
}

const areSentencesSimilar = solve;
class Solution {
  areSentencesSimilar(sentence1, sentence2) { return solve(sentence1, sentence2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, areSentencesSimilar };
