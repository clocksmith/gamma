'use strict';

// 3615. Longest Palindromic Path in Graph.
// Extend palindromic paths at both endpoints using unused equal-label neighbors and subset memoization; O(2^n*n^4) worst-case time and O(2^n*n^2) space. Inputs are preserved.

function solve(n, edges, label) {
  const adjacent = new Int32Array(n), labels = new Int32Array(26), size = 1 << n, full = size - 1;
  for (let node = 0; node < n; node += 1) labels[label.charCodeAt(node) - 97] |= 1 << node;
  for (const [first, second] of edges) { adjacent[first] |= 1 << second; adjacent[second] |= 1 << first; }
  const memo = new Uint8Array(size * n * n), population = new Uint8Array(size);
  for (let mask = 1; mask < size; mask += 1) population[mask] = population[mask >> 1] + (mask & 1);
  function visit(mask, first, last) {
    if (first > last) [first, last] = [last, first];
    const identity = (mask * n + first) * n + last;
    if (memo[identity]) return memo[identity];
    let best = population[mask];
    const upper = n - (n - best) % 2, available = full ^ mask;
    let left = adjacent[first] & available;
    while (left) {
      const bit = left & -left, node = 31 - Math.clz32(bit);
      left ^= bit;
      let right = adjacent[last] & available & labels[label.charCodeAt(node) - 97] & ~bit;
      while (right) {
        const otherBit = right & -right, other = 31 - Math.clz32(otherBit);
        right ^= otherBit;
        best = Math.max(best, visit(mask | bit | otherBit, node, other));
        if (best === upper) { memo[identity] = best; return best; }
      }
    }
    memo[identity] = best;
    return best;
  }
  let answer = 1;
  for (let node = 0; node < n; node += 1) answer = Math.max(answer, visit(1 << node, node, node));
  for (const [first, second] of edges) if (label[first] === label[second]) answer = Math.max(answer, visit((1 << first) | (1 << second), first, second));
  return answer;
}

const maxLen = solve;
class Solution {
  maxLen(n, edges, label) { return solve(n, edges, label); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxLen };
