'use strict';

// 3485. Longest Common Prefix of K Strings After Removal: count qualified trie prefixes by depth and retract only uniquely fragile depths.
// O(S + n) expected time and O(S + n) space, S=total word length. Inputs are preserved.
function solve(words, k) {
  const n = words.length;
  if (n - 1 < k) return Array(n).fill(0);
  const children = [new Map()];
  const count = [0];
  const depth = [0];
  let maximumDepth = 0;
  for (const word of words) {
    let node = 0;
    for (const character of word) {
      if (!children[node].has(character)) {
        children[node].set(character, children.length);
        children.push(new Map());
        count.push(0);
        depth.push(depth[node] + 1);
        maximumDepth = Math.max(maximumDepth, depth[node] + 1);
      }
      node = children[node].get(character);
      count[node] += 1;
    }
  }
  const qualified = new Int32Array(maximumDepth + 1);
  let best = 0;
  for (let node = 1; node < children.length; node += 1) {
    if (count[node] >= k) {
      qualified[depth[node]] += 1;
      best = Math.max(best, depth[node]);
    }
  }
  const answer = [];
  for (const word of words) {
    const fragile = new Set();
    let node = 0;
    for (const character of word) {
      node = children[node].get(character);
      if (count[node] === k && qualified[depth[node]] === 1) fragile.add(depth[node]);
    }
    let result = best;
    while (fragile.has(result)) result -= 1;
    answer.push(result);
  }
  return answer;
}

const longestCommonPrefix = solve;
class Solution {
  longestCommonPrefix(words, k) { return solve(words, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestCommonPrefix };
