'use strict';

// 1554. Strings Differ by One Character: identify exact prefix and suffix pairs with trie-state identities.
// O(S) expected time and O(S) space for S total characters; no probabilistic hashes; inputs are read-only.
function solve(dict) {
  const prefixEdges = new Map();
  const suffixEdges = new Map();
  const removed = new Map();
  for (const word of dict) {
    const suffixes = new Int32Array(word.length + 1);
    for (let index = word.length - 1; index >= 0; index -= 1) {
      const transition = `${suffixes[index + 1]}:${word[index]}`;
      if (!suffixEdges.has(transition)) suffixEdges.set(transition, suffixEdges.size + 1);
      suffixes[index] = suffixEdges.get(transition);
    }
    let prefix = 0;
    for (let index = 0; index < word.length; index += 1) {
      const char = word[index];
      const signature = `${prefix}:${suffixes[index + 1]}`;
      if (removed.has(signature) && removed.get(signature) !== char) return true;
      removed.set(signature, char);
      const transition = `${prefix}:${char}`;
      if (!prefixEdges.has(transition)) prefixEdges.set(transition, prefixEdges.size + 1);
      prefix = prefixEdges.get(transition);
    }
  }
  return false;
}

const differByOne = solve;
class Solution {
  differByOne(dict) { return solve(dict); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, differByOne };
