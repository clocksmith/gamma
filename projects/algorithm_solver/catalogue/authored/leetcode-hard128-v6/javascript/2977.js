'use strict';

// 2977. Minimum Cost to Convert String II.
// All-pairs conversion costs plus trie-guided prefix DP; O(U^3+n*L+S) time, O(U^2+n+S) space. Inputs are preserved.

function solve(source, target, original, changed, cost) {
  const words = [...new Set(original.concat(changed))], identity = new Map(words.map((word, index) => [word, index])), size = words.length;
  const distance = Array.from({ length: size }, (_, i) => Array.from({ length: size }, (_, j) => i === j ? 0 : Infinity));
  for (let i = 0; i < original.length; i += 1) {
    const a = identity.get(original[i]), b = identity.get(changed[i]);
    distance[a][b] = Math.min(distance[a][b], cost[i]);
  }
  for (let middle = 0; middle < size; middle += 1) {
    for (let a = 0; a < size; a += 1) {
      if (distance[a][middle] === Infinity) continue;
      for (let b = 0; b < size; b += 1) distance[a][b] = Math.min(distance[a][b], distance[a][middle] + distance[middle][b]);
    }
  }
  const children = [new Map()], terminal = [-1];
  for (const [word, index] of identity) {
    let state = 0;
    for (const char of word) {
      if (!children[state].has(char)) { children[state].set(char, children.length); children.push(new Map()); terminal.push(-1); }
      state = children[state].get(char);
    }
    terminal[state] = index;
  }
  const best = Array(source.length + 1).fill(Infinity); best[0] = 0;
  for (let start = 0; start < source.length; start += 1) {
    if (best[start] === Infinity) continue;
    if (source[start] === target[start]) best[start + 1] = Math.min(best[start + 1], best[start]);
    let a = 0, b = 0;
    for (let end = start; end < source.length; end += 1) {
      a = children[a].get(source[end]); b = children[b].get(target[end]);
      if (a === undefined || b === undefined) break;
      if (terminal[a] !== -1 && terminal[b] !== -1) best[end + 1] = Math.min(best[end + 1], best[start] + distance[terminal[a]][terminal[b]]);
    }
  }
  return best[source.length] === Infinity ? -1 : best[source.length];
}

const minimumCost = solve;
class Solution {
  minimumCost(source, target, original, changed, cost) { return solve(source, target, original, changed, cost); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumCost };
