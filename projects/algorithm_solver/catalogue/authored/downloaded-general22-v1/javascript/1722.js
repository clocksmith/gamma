'use strict';

// 1722. Minimize Hamming Distance After Swap Operations (Medium).
// Specification: https://leetcode.com/problems/minimize-hamming-distance-after-swap-operations/description/
function solve(source, target, allowedSwaps) {
  const n = source.length;
  const parent = [];
  for (let i = 0; i < n; i++) parent.push(i);
  function find(x) { while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; }
  for (const [a, b] of allowedSwaps) parent[find(a)] = find(b);
  const groups = new Map();
  for (let i = 0; i < n; i++) {
    const root = find(i);
    if (!groups.has(root)) groups.set(root, []);
    groups.get(root).push(i);
  }
  let answer = 0;
  for (const indices of groups.values()) {
    const counts = new Map();
    for (const i of indices) counts.set(source[i], (counts.get(source[i]) || 0) + 1);
    for (const i of indices) {
      const value = target[i];
      if ((counts.get(value) || 0) > 0) counts.set(value, counts.get(value) - 1);
      else answer++;
    }
  }
  return answer;
}
const minimumHammingDistance = solve;
class Solution { minimumHammingDistance(source, target, allowedSwaps) { return solve(source, target, allowedSwaps); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumHammingDistance };
