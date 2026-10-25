'use strict';

// O(S) time/space: a node has at most 26 siblings. No per-node object allocation.
function solve(words) {
  let capacity = 1;
  for (const word of words) capacity += word.length;
  const first = new Int32Array(capacity).fill(-1);
  const sibling = new Int32Array(capacity).fill(-1);
  const counts = new Uint32Array(capacity);
  const letters = new Uint8Array(capacity);
  let used = 1;
  for (const word of words) {
    let node = 0;
    for (let index = 0; index < word.length; index += 1) {
      const code = word.charCodeAt(index) - 97;
      let child = first[node];
      while (child !== -1 && letters[child] !== code) child = sibling[child];
      if (child === -1) {
        child = used;
        used += 1;
        letters[child] = code;
        sibling[child] = first[node];
        first[node] = child;
      }
      counts[child] += 1;
      node = child;
    }
  }
  return words.map(word => {
    let node = 0;
    let score = 0;
    for (let index = 0; index < word.length; index += 1) {
      const code = word.charCodeAt(index) - 97;
      let child = first[node];
      while (letters[child] !== code) child = sibling[child];
      score += counts[child];
      node = child;
    }
    return score;
  });
}

const sumPrefixScores = solve;
class Solution {
  sumPrefixScores(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumPrefixScores };
