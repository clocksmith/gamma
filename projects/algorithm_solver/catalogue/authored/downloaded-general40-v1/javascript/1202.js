'use strict';

// 1202. Smallest String With Swaps (Medium).
// Specification: https://leetcode.com/problems/smallest-string-with-swaps/description/
function solve(s, pairs) {
  const n = s.length;
  const parent = Array.from({ length: n }, (_, i) => i);
  function find(x) { while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; }
  function union(a, b) { parent[find(a)] = find(b); }
  for (const [a, b] of pairs) union(a, b);
  const groups = {};
  for (let i = 0; i < n; i++) { const root = find(i); if (!groups[root]) groups[root] = []; groups[root].push(i); }
  const result = s.split('');
  for (const root in groups) {
    const indices = groups[root].sort((a, b) => a - b);
    const chars = indices.map((i) => s[i]).sort();
    indices.forEach((index, position) => { result[index] = chars[position]; });
  }
  return result.join('');
}
const smallestStringWithSwaps = solve;
class Solution { smallestStringWithSwaps(s, pairs) { return solve(s, pairs); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestStringWithSwaps };
